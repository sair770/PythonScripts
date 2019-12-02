from PIL import Image
import mechanize
from mechanize import Browser
from bs4 import BeautifulSoup
import json, timeit,os
from cap import resolve
import http.cookiejar as cookielib
import urllib
import time
import os
import pytesseract
import sys
import argparse
try:
    import Image
except ImportError:
    from PIL import Image
from subprocess import check_output

global url
url = "http://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do"

def resolve(path):
    #Uses tessaract ocr to solve captcha
	check_output(['convert', path, '-resample', '600', path])
	return pytesseract.image_to_string(Image.open(path))

def removeextras(_val):
    #Removes extra spaces,newlines and tabs
    if _val:
        try:
            _val = _val.text.replace("  ","").replace("\n","").replace("\t","").strip()
        except:
            _val = _val.replace("  ","").replace("\n","").replace("\t","").strip()
    
    return _val

def extractHeaderTable(_trs):
    """Extracts tables which have headers
    Arguments : BeautifulSoup obj of all the trs under a table
    Returns : json 
    Format : [
        {"header1":value1,"header2":value2,"header3":value3},
        {"header1":value1,"header2":value2,"header3":value3}
    ]
    """
    _json = [] 
    _headers =[x.text for x in _trs[0].find_all("th")]
    for tr in _trs[1:]:
        txt = [removeextras(x) for x in tr.find_all("td")]
        _tmp = {_headers[num]:removeextras(y) for num,y in enumerate(txt)}
        _json.append(_tmp)
    
    return _json
        
def extractTable(_trs):
    """Extracts
    
    Arguments:
        _trs  -- BeautifulSoup obj of all the trs under a table
    
    Returns:
        [json] -- return normal key:value dictionary
    """
    _json = {}
    _tds = [_tr.find_all("td") for _tr in _trs]
    _json = {removeextras(_td[0]):removeextras(_td[1]) for _td in _tds}

    return _json

def tableToJson(_table):
    """tries to identify the type of table and returns json
    
    Arguments:
        _table  -- BeautifulSoup obj of the  table
    
    Returns:
        [json] -- returns normal key:value dictionary
    """
    _json = {}
    trs = _table.find_all("tr")

    if ("<th>" in str(trs[0])) and ("</th>" in str(trs[0])):
        _json = extractHeaderTable(trs)
    else:
        _json = extractTable(trs)

    print(_json)
    return _json


def getBrowser():
    """Create mechanize browser object
    
    Returns:
        [browser obj] -- returns browser obj
    """
    cj = cookielib.CookieJar()
    br= mechanize.Browser()
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_cookiejar(cj)
    br.set_header("User-Agent"," Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0")
    return br

def solve_captcha(br,url):
    """Fetchs the webpage,captcha image and tries to solve the captcha
    
    Arguments:
        br  -- browser object
        url  -- url
    
    Returns:
        [str] -- solved captcha, "" if couldnt solve it
    """
    print("Fetching the page")
    r=br.open(url)
    html=r.read()
    soup=BeautifulSoup(html,features="html5lib")
    im = soup.find('img', id='captcha')
    image_response = br.open_novisit(im['src'])
    k = image_response.read()
    c_file = "captcha.jpeg"
    with open(c_file,"wb") as f:
        f.write(k)
        f.close()
    print("Solving captcha")
    starttime = timeit.default_timer()
    captcha = resolve(c_file)
    stoptime = timeit.default_timer()
    captcha = captcha.lower().replace(" ","")

    return captcha

def fetchresponse(url,cin,save):
    """tries to solve the captcha multiple times until we get a string 
        and uses that to submit the cin number to the page
    
    Arguments:
        url  -- url of the page
        cin  -- cin number of the company
        save  -- Save the response html page if True
    
    Returns:
        [str] -- Response HTML page
    """
    br = getBrowser()
    captcha = None
    while not captcha:
        captcha = solve_captcha(br,url)
        if not captcha:
            print("couldnt parse captcha correctly trying again after 1 sec")
            time.sleep(1)

    print("fetching")
    br.select_form(nr=2)
    br.form['companyID'] = cin
    br.form['userEnteredCaptcha']=captcha
    resp = br.submit().read().decode("utf-8")
    
    if save:
        savefile(resp,cin,"html")
        

    return resp

def checkdata(resp):
    """checks if the response page from fetchresponse function contains the data
    
    Arguments:
        resp {[type]} -- HTML string
    
    Returns:
        [Bool] -- True if the data is present else false
    """
    if "Enter Characters shown below :" in resp:
        #If this string is present in the page it means the captcha was wrong
        return False

    soup = BeautifulSoup(resp,"html.parser")
    _res = soup.find("table",id="resultTab1")
    #another check to see if the table actually containing the data is present
    return bool(_res)

def savefile(_data,_filename,_format="json"):
    """Saves the file to the disk in results folder
    
    Arguments:
        _data  -- data that needs to be saved to file
        _filename  -- filename without extension
    
    Keyword Arguments:
        _format  -- Format/extension of the file (default: {"json"})
    """
    try:
        if _format=="json":
            _data = json.dumps(_data,indent=4)

        path = os.path.join("results",_filename+"."+_format)
        with open(path,"w") as f:
            f.write(_data)
    except Exception as e:
            print(e)
            print("***************FILE STARTS******************")
            print(_data)
            print("***************FILE END******************")

def getDetails(resp):
    """function which fetchs the company data and director data tables 
        and passes to the tableToJson function to get json
    
    Arguments:
        resp  -- HTML string
    
    Returns:
        [json] -- {
            "company":{}
            "directors:[{},{},{}]
        }
    """
    soup = BeautifulSoup(resp,"html.parser")
    _json = {}

    companydata = "resultTab1"
    directors = "resultTab6"

    companytable = soup.find("table",id=companydata)
    directorstable = soup.find("table",id=directors)

    companyjson = tableToJson(companytable)
    if companyjson:
        _json["company"] = companyjson

    directorsjson = tableToJson(directorstable)
    if directorsjson:
        _json["directors"] = directorsjson
    
    return _json

def extractdata(url,cin,save=True):
    """Kinda like the main function
    
    Arguments:
        url  -- URL of the page
        cin  -- cin number
    
    Keyword Arguments:
        save {bool} -- if True saves the response and json to results folder (default: {True})
    
    Returns:
        [json] -- json
    """
    check = False
    while check==False:
        _resp = fetchresponse(url,cin,save=True)
        check = checkdata(_resp) 
        if not check:
            print("No data found or wrong captcha trying again after 1 sec")
            time.sleep(1)

    _json = getDetails(_resp)
    
    if save:
        savefile(_json,cin)
    
    return _json

def extractfile(url,path):
    """Same as extractdata function but takes cin numbers from file path
    
    Arguments:
        path  -- path to the text file
    """
    with open(path) as f:
        _text = f.read()
    
    _text = _text.split()
    for num,cin in enumerate(_text):
        print("Extracting and saving data for index: {} ,cin: {}\n\n".format(num,cin))
        _json = extractdata(url,cin)
        time.sleep(2)

    print("Done")

    
if __name__=="__main__":
    if not os.path.isdir("results"):
        os.mkdir("results")
    
    argparser = argparse.ArgumentParser()
    argparser.add_argument('cin',help = 'CIN Number')
    argparser.add_argument('-f','--file',help = 'path to txt file containing cins',action="store_true")
    args = argparser.parse_args()
    cin = args.cin
    _file = args.file

    if _file:
        print("extracting data from file: {}\n\n".format(cin))
        extractfile(url,cin)
    else:
        print("extracting data for cin: {}\n\n".format(cin))
        extractdata(url,cin)

