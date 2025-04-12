from django.shortcuts import render, redirect
from .forms import NewsForm, ReviewForm
from .models import Other_news, StockSymbol
from django.utils.timezone import now
from datetime import datetime, timedelta
from django.contrib import messages
import requests
import pandas as pd
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import yfinance as yf
from io import StringIO
from requests.exceptions import ConnectionError 
import requests
from django.contrib.auth import authenticate, login as login_user, logout, get_user_model
from django.contrib.auth.decorators import login_required

#function to update symbols
def fetch_and_store_symbols():
    """
    Fetch stock symbols from Wikipedia (S&P 500), NASDAQ, and NSE, clean them,
    and store them in the database without duplicates.
    """
    sources = {
        "sp500": {
            "url": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            "columns": ["Symbol", "Security"],
            "rename": {"Symbol": "symbol", "Security": "security_name"},
        },
        "nasdaq": {
            "url": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt",
            "columns": ["Symbol", "Security Name"],
            "rename": {"Symbol": "symbol", "Security Name": "security_name"},
            "filter": ("Test Issue", "N"),  # Keep only active stocks
        },
        "nse": {
            "url": "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv",
            "columns": ["SYMBOL", "NAME OF COMPANY"],
            "rename": {"SYMBOL": "symbol", "NAME OF COMPANY": "security_name"},
            "append": ".NS",  # Add `.NS` suffix to NSE symbols
        }
    }

    new_stocks = []

    for source, config in sources.items():
        try:
            if source == "sp500":
                df = pd.read_html(config["url"])[0]
            else:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(config["url"], headers=headers)
                if response.status_code != 200:
                    continue
                df = pd.read_csv(StringIO(response.text), sep="|" if source == "nasdaq" else ",")

            df = df[config["columns"]].rename(columns=config["rename"])

            if "filter" in config:
                df = df[df[config["filter"][0]] == config["filter"][1]]

            if "append" in config:
                df["symbol"] = df["symbol"].astype(str) + config["append"]

            new_stocks.extend(df.to_dict(orient="records"))

        except Exception as e:
            print(f"Error fetching {source} data: {e}")

    if not new_stocks:
        return 0  # No new data fetched

    # Fetch existing symbols from the database
    existing_symbols = set(StockSymbol.objects.values_list("symbol", flat=True))

    # Filter out duplicates
    unique_stocks = [StockSymbol(**stock) for stock in new_stocks if stock["symbol"] not in existing_symbols]

    # Bulk insert new symbols
    StockSymbol.objects.bulk_create(unique_stocks)

    return len(unique_stocks)  # Return count of newly added symbols



# funtion to gets time since
def time_since(date):
    today = now().date()
    delta = today - date

    if delta.days == 0:
        return "Today"
    elif delta.days == 1:
        return "Yesterday"
    elif delta.days < 7:
        return f"{delta.days} days ago"
    elif delta.days < 30:
        weeks = delta.days // 7
        return f"{weeks} week ago" if weeks == 1 else f"{weeks} weeks ago"
    elif delta.days < 365:
        months = delta.days // 30
        return f"{months} month ago" if months == 1 else f"{months} months ago"
    else:
        years = delta.days // 365
        return f"{years} year ago" if years == 1 else f"{years} years ago"

# Create your views here.
def stock_news_other(request):

    date_filter=request.GET.get("date"," ")
    current_date= datetime.now().strftime("%Y-%m-%d")
    status=""
    news=Other_news.objects.all().order_by('-date')
    
    
    if date_filter==" ":
        news
    elif date_filter >= current_date:
        messages.success(request, f"Date should be before {current_date}.")
        status='danger'
    
    elif date_filter=="":
        news
        messages.success(request, f"Sucessfully loaded all news")
        status='success'
        
    elif date_filter<= "2025-02-03":
        messages.success(request, f"Please select date after 2025-02-03.")
        status='danger'
        
        
    else:
        # print(date)
        news=Other_news.objects.filter(date=date_filter)
        if len(news)==0:
            messages.success(request, f"No news on date {date_filter}")
            status='danger'
        else:
            messages.success(request, f"Filtered Sucessfully on date {date_filter}")
            status='success'
    
    for items in news:
        items.relative_date=time_since(items.date)
        
    paginator=Paginator(news,10)
    
    page_no= request.GET.get("page")
    
    page_news=paginator.get_page(page_no)
    
    return render(request, 'stock_news_others.html', {'news':page_news, "status":status,})

# news with sentiments
def stock_news(request):
    
    api_url="https://newsapi-production-178e.up.railway.app/news/"
    
    sentiment_filter=request.GET.get("sentiment","")
    
    if sentiment_filter:
        api_url=f"https://newsapi-production-178e.up.railway.app/news/?sentiment={sentiment_filter}"
        # print('filtered', api_url)
    
    try:
        # print('try', api_url)
        response=requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()  # Convert response to JSON
            # data= data.get('results', [])
            for item in data:
                item["date"] = datetime.strptime(item["date"], "%Y-%m-%d").date()  # Convert string to date
                item["relative_date"] = time_since(item["date"])  # Apply function
            # data = sorted(data, key=lambda x: x.get('id', 0))  # Sort by 'id' (descending)
            
            page= request.GET.get("page", 1)
            paginator = Paginator(data, 5)
            
            try:
                data= paginator.page(page)
            except PageNotAnInteger:
                data= paginator.page(1)
            except EmptyPage:
                data= paginator.page(paginator.num_pages)
                            
        else:
            data = {"error": "Failed to fetch data"}
    except ConnectionError:
        data = {"error": "API is not reachable. Please try again later."}
        
    # data=News.objects.all()
    
    return render(request, 'stock_news.html', {'news':data})

def news_content(request, news_id):
    
    api_url = f"https://newsapi-production-178e.up.railway.app/news/{news_id}/"
    
    # news_content=get_object_or_404(News, id=news_id)
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        news_content = response.json()
        news_content["date"] = datetime.strptime(news_content["date"], "%Y-%m-%d").date()  # Convert string to date
        
    except requests.exceptions.RequestException as e:
        news_content = None
        print(f"Error fetching news content: {e}")  # Log the error
    
    return render(request, 'news_content.html', {'news':news_content})


def stock_detail(request):
    # Default stock symbol
    session = requests.Session() 
    symbol = "AAPL"

    # If form is submitted, get stock name
    if request.method == 'POST':
        selected_stock_name = request.POST.get('stock_name', '')
        stock = StockSymbol.objects.filter(security_name=selected_stock_name).first()
        if stock:
            symbol = stock.symbol  # Update symbol if found

    # Fetch stock details
    stock_detail = yf.Ticker(symbol, session=session)
    dividend = stock_detail.dividends.reset_index()[['Date','Dividends']].tail(5).iloc[::-1]
    dividend['Date']=dividend['Date'].dt.strftime('%d %B %Y')
    dividend=dividend.to_dict(orient='records')
    # print(stock_detail)
    # print(dividend)
    split = stock_detail.splits.reset_index()[['Date','Stock Splits']].tail(5).iloc[::-1]
    split.columns = ['Date', 'Splits']  # Rename column for avoiding error
    split['Date']=split['Date'].dt.strftime('%d %B %Y')
    split=split.to_dict(orient='records')
    # print(stock_detail)
    # print(split)
    history = stock_detail.history(period="5d")
    # print(history)

    # Default values
    # stock_name = stock_detail.info.get('shortName', '')
    
    info=stock_detail.info
    
    try:
        analyst_rec = stock_detail.recommendations.iloc[0]
    except:
        analyst_rec = {
                "strongBuy": "N/A",
                "buy": "N/A",
                "hold": "N/A",
                "sell": "N/A",
                "strongSell": "N/A",
            }


    # If history exists, extract stock data
    if not history.empty:
        as_on_date = history.index[-1].strftime('%B %d, %Y (%A)')  # Latest date
        stock_price = round(history['Close'].iloc[-1], 2)
        
        # Determine price trend (up/down)
        differance=stock_detail.info.get('regularMarketChange','')
        diff_tri_color, diff_tri = ('green', '▲') if differance > 0 else ('red', '▼')
    else:
        as_on_date = stock_price=differance = diff_tri_color = history_data=analyst_rec=diff_tri = ''

    # Fetch stock list for dropdown
    stock_list = StockSymbol.objects.all()
    history_data = history.reset_index()[['Date', 'Open', 'High', 'Low', 'Close']].round(2).values.tolist()[::-1]
    
    inst_hold = stock_detail.institutional_holders

    # Check if institutional holders exist and is not empty
    if isinstance(inst_hold, pd.DataFrame) and not inst_hold.empty:
        # inst_hold.columns = ['Date','Holder',  'pctHeld', 'Shares', 'Value']
        inst_hold = inst_hold.to_dict(orient='records')  # Convert DataFrame to a list of dictionaries
    else:
        inst_invt = []  # Ensure it's always a list
        
    mf_hold = stock_detail.mutualfund_holders

    # Check if institutional holders exist and is not empty
    if isinstance(mf_hold, pd.DataFrame) and not mf_hold.empty:
        # mf_hold.columns = ['Date','Holder',  'pctHeld', 'Shares', 'Value']
        mf_hold = mf_hold.to_dict(orient='records')  # Convert DataFrame to a list of dictionaries
    else:
        mf_hold = []  # Ensure it's always a list

    kp_df = pd.DataFrame(info.get('companyOfficers', []))[['name', 'title']]
    kp_list = kp_df.to_dict(orient='records')  # Convert to list of dictionaries
    
    # Convert debtToEquity from percentage to ratio
    info['debtToEquity'] = info.get('debtToEquity', 0) / 100 

    # print(kp_df)

    # Pass data to template
    return render(request, 'stock_detail.html', {
        'list': stock_list, 'as_on_date': as_on_date,
        'stock_price': stock_price, 'differance': differance, 'diff_tri_color': diff_tri_color, 'diff_tri': diff_tri, 'history_data':history_data, 'analyst_rec':analyst_rec, 'dividend':dividend, 'split':split, 'inst_invt':inst_hold, 'mf_hold':mf_hold, 'info':info, 'kp_df':kp_list
    })

# comment function 
def review(request):
    
    api_url="https://newsapi-production-178e.up.railway.app/"
    api_url_create="https://newsapi-production-178e.up.railway.app/create/"
    # print('api')
    
    try:
        response=requests.get(api_url)
        # print('request done')
        
        if response.status_code == 200:
            data = response.json()  # Convert response to JSON
            # print(data)
            page= request.GET.get("page", 1)
            paginator= Paginator(data, 5)
            
            try:
                data = paginator.page(page)
            except PageNotAnInteger:
                data = paginator.page(1)
            except EmptyPage:
                data = paginator.page(paginator.num_pages)
            
        else:
            data = {"error": "Failed to fetch data"}
    except ConnectionError:
        data = {"error": "API is not reachable. Please try again later."}
    except requests.exceptions.JSONDecodeError:
        data = {"error": "API port not working"}
        
        
    # make form to get comment and save comment in api 
    # form=ReviewForm()
    
    if request.method=='POST':
        
        form=ReviewForm(request.POST)
        
        if form.is_valid():
            form_data= form.cleaned_data # get clean data from form
            
            # prepare jason data to sent to API 
            save_comment = {
                "fname": form_data["fname"],
                "lname": form_data["lname"],
                "email": form_data["email"],
                "comment": form_data["comment"],
                "exp": form_data["exp"]  # `exp` is the rating field
            }
            
            #send post request to api
            try:
                response=requests.post(api_url_create, json=save_comment)
                # print('request done')
                
                if response.status_code in [200, 201]:
                    print("Comment saved successfully!")
                    return redirect('review')  # Redirect to refresh the page
                else:
                    data = {"error": "Failed to save data"}
            except ConnectionError:
                data = {"error": "API is not reachable. Please try again later."}
                
            except requests.exceptions.ConnectionError as other:
                print("Unexpected error while trying to connect to API", other)
    else:
        form=ReviewForm()
        
    return render(request, "review.html", {"data": data, "form": form})

def contact_us(request):
    return render(request, 'contact_us.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remmember=request.POST.get('remmember')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login_user(request, user)
            print(user,'user')
            
            if remmember:
                request.session.set_expiry(2592000)  # 30 days in seconds
            else:
                request.session.set_expiry(0) # Session expires on browser close
            
            return redirect('other_news')
        else:
            print('user not found')
            messages.error(request, 'Invalid username or password.')
        
        
    return render(request, 'login.html')    

@login_required(login_url='/')
def edit_news(request):
    news_id = request.GET.get('get_record') or request.POST.get('record_id')  # Ensure news_id is set
    get_record = None
    api_url = f"https://newsapi-production-178e.up.railway.app/news/{news_id}/" if news_id else None

    if news_id and request.method == "GET":  # Fetch news details only on GET
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                get_record = response.json()
            else:
                messages.error(request, "Failed to fetch news data.")
        except requests.exceptions.RequestException:
            messages.error(request, "API request failed.")

    if request.method == "POST" and news_id:
        action = request.POST.get("action")  # Check if it's edit or delete

        if action == "edit":
            updated_data = {
                "date": request.POST.get("date"),
                "head": request.POST.get("head"),
                "sub_head": request.POST.get("sub_head"),
                "image_link": request.POST.get("image_link"),
                "content": request.POST.get("content"),
                "sentiment": request.POST.get("sentiment"),
            }
            
            try:
                response = requests.put(api_url, json=updated_data)
                if response.status_code == 200:
                    # messages.success(request, "News updated successfully!")
                    return redirect("news")  #Redirect to stock_news page
                # else:
                #     messages.error(request, "Error updating news.")
            except requests.exceptions.RequestException:
                messages.error(request, "API request failed.")

        elif action == "delete":
            try:
                response = requests.delete(api_url)
                if response.status_code == 204:
                    # messages.success(request, "News deleted successfully!")
                    return redirect("news")  #Redirect to stock_news page
                # else:
                #     messages.error(request, "Error deleting news.")
            except requests.exceptions.RequestException:
                messages.error(request, "API request failed.")

    return render(request, 'edit_news.html', {'get_record': get_record})

@login_required(login_url='/')
def news_control(request):
    form=NewsForm(request.POST)
    
    try:
        api_url = "https://newsapi-production-178e.up.railway.app/news/"  # API endpoint
        response = requests.get(api_url)
        if response.status_code == 200:
            news_list = response.json()  # Convert response to JSON
        else:
            news_list = [] 
        
        if request.method == 'POST':
            #Extract form data
            news_data = {
                'date': request.POST.get('date'),
                'head': request.POST.get('head'),
                'sub_head': request.POST.get('sub_head'),
                'image_link': request.POST.get('image_link'),
                'content': request.POST.get('content'),
                # 'sentiment': request.POST.get('sentiment')
            }
            response = requests.post(api_url, json=news_data)  # Send data to API

            if response.status_code == 201:  # 201 = Created Successfully
                print('created')
                return redirect('control')  #Redirect after success
            else:
                error_message = response.json()  # Get API error message
                print('not created')
                return render(request, 'news_control.html', {'form': form, 'error': error_message})
    except requests.exceptions.RequestException as e:
        error_message = "error in rendering API"
        return render(request, 'news_control.html', {'form': form, 'error': error_message})
    # return render(request, 'stock_news.html')  # Show form if method is GET
    return render(request, 'news_control.html',{'form':form, 'n_list':news_list})   

    
    # if request.method=='POST':
    #     form=NewsForm(request.POST)
    #     print(form)
    #     # if form.is_valid():                
    #     #     form.save()
    #     #     return redirect('control')
    #     # else:
    #     #     print(form.errors)
    # else:
    #     form=NewsForm()
    # return render(request, 'news_control.html',{'form':form})

@login_required(login_url='/')
def auto_process_news(request):
    
    alert=None
    if request.method=="POST":
        
        # Get the current date and subtract one day to get yesterday
        # current_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        current_date= request.POST.get("date")
        
        if not current_date:
            current_date=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        
        news_api_key='210cf3771b13428482ff21e34c6ba1ab'
        
        news_articles=0
        
        url=f"https://newsapi.org/v2/everything?q=stock+market&from={current_date}&to={current_date}&language=en&sortBy=popularity&apiKey={news_api_key}"
        
        response = requests.get(url)
        news_data = response.json()

        
        # check if data present in news_data
        if 'articles' in news_data:
            for article in news_data['articles'][:5]:
                #it will not save news if image is not present in it
                if not article.get('urlToImage'):
                    continue
                
                #check if same news is present in our db
                existing_news=Other_news.objects.filter(
                    head=article['title'],
                    sub_head=article['description'],
                    source=article['source']['name'],
                    news_link=article['url']
                ).exists()
                
                if not existing_news:
                    news=Other_news(
                        date=current_date,
                        head=article['title'],
                        sub_head=article['description'],
                        source=article['source']['name'],
                        image_link=article['urlToImage'],
                        news_link=article['url'],                        
                    )
                    
                    news.save()
                    news_articles +=1
            print(news_articles)
                    
            #success and progress message
            if news_articles > 0:
                alert='success'
                messages.add_message(request, messages.SUCCESS,f"Successfully processed {news_articles} news articles.", extra_tags="news")
            else:
                alert='danger'
                messages.add_message(request, messages.SUCCESS, f"No new news articles to process.", extra_tags="news")
        else:
            alert='danger'
            messages.add_message(request, messages.SUCCESS, f"No articles found. Response: {news_data['message']}", extra_tags="news")
            
        form=NewsForm()
        
        return render(request, 'news_control.html', {'alert':alert, 'form':form})    

    form=NewsForm()
    
    return render(request, 'news_control.html', {'alert':alert, 'form':form})

@login_required(login_url='/')
def auto_process_symbols(request):
    """
    View function to handle button click and import stock symbols.
    """
    new_count = fetch_and_store_symbols()

    if new_count > 0:
        messages.success(request, f"Stock symbols imported successfully! New stocks added: {new_count}", extra_tags="symbol")
    else:
        messages.error(request, "No new data was added.", extra_tags="symbol")

    return render(request, "news_control.html", {"alert": "success" if new_count else "danger", "form": NewsForm()})    

@login_required(login_url='/')
def logout_view(request):
    logout(request)
    return redirect('other_news')