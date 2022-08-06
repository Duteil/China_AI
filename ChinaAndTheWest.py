# -*- coding: utf-8 -*-
"""
This script aims to compare the topic of research in AI 
in the West and in China.
Journals were chosen as those in the field of AI with 
the highest H-index as presented in this page:
https://www.scimagojr.com/journalrank.php?category=1702&order=h&ord=desc

"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import ast
import os
from datetime import date
import pickle


jidx = ['west1', 
       'west2', 
       'west3', 
       #'west4',  # Removed because the keywords do not appear on the main page.
       'west5', 
       'west6', 
       # 'west7', Removed from the data set, as there are no keywords to analyse.
       'west8', 
       'west9',
       #'china1', # I do not understand how the issues or article are sorted in the source code for the main page.
       'china2', 
       'china3', 
       'china4', 
       # 'china5', Removed from the data set, as there are no keywords to analyse.
       'china6', 
       'china7', 
       'china8', 
       'china9']


journals_nb = 14 #17 # number of journals we're considering, up to 18
journals_nb = min(journals_nb,len(jidx)-1)

def find_nth(text, word, n):
    start = text.find(word)
    while start >= 0 and n > 1:
        start = text.find(word, start+len(word))
        n -= 1
    return start

def vocabulary(topic,radical,words_list):
    for word in words_list:
        if radical in word.lower():
            topic.add(word)
    return topic


def get_issue_dblp(journal_url):
    issues_list = []
    html_issue_data  = requests.get(journal_url).text
    soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
    for link in soup_issue.find_all('a', href=True):
        tag_str = str(link)
        # Checking that the formatting of the link matches a link to an issue of a journal in the DBLP:
        if tag_str[:38] == '<a href="https://dblp.org/db/journals/' and tag_str[-6:-4].isdigit(): #tag_str.find('.html') > 0 :
            url_start = tag_str.find("href=") + 6
            url_end = tag_str.find('">')
            new_link = tag_str[url_start:url_end]
            if new_link not in issues_list:
                issues_list.append(new_link)
    return issues_list


def get_article_dblp(issue_url, years):
    link_list = []
    year = 0
    html_issue_data  = requests.get(issue_url).text
    soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
    year = int(str(soup_issue.find_all('h2')[1])[-9:-5])
    if year >= years[0]:
        for link in soup_issue.find_all('a', href=True):
            if "https://doi.org" in str(link):
                tag_str = str(link)
                if"><" in tag_str:
                    link_start = 9
                    link_end = find_nth(tag_str, "\"", 2)
                    new_link = tag_str[link_start:link_end]
                    if new_link not in link_list:
                        link_list.append(new_link)
    return year, link_list


def get_article_jiqiren(issue_url, years):
    link_list = []
    year = 0
    html_issue_data  = requests.get(issue_url).text
    soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
    year = int(str(soup_issue.find_all('strong')[1])[8:12])
    if year >= years[0]:
        for link in soup_issue.find_all('a', href=True):
            if '<a href="http://robot.sia.cn/EN/' in str(link):
                tag_str = str(link)
                link_start = 9
                link_end = find_nth(tag_str, "\"", 2)
                if tag_str[link_end-2:link_end].isdigit():
                    new_link = tag_str[link_start:link_end]
                    if new_link not in link_list:
                        link_list.append(new_link)
    return year, link_list


def get_issue_jiqiren(journal_url):
    ''' 
    The issues on Jiqiren have a simple structure: 
    http://robot.sia.cn/EN/volumn/volumn_X.shtml, where X is a number.
    '''
    radical = 'http://robot.sia.cn/EN/'
    volume_str = 'volumn/volumn_'
    issues_list = []
    html_journal_data  = requests.get(journal_url).text
    soup_journal = BeautifulSoup(html_journal_data, 'html.parser')
    issues = soup_journal.find_all('a')
    a = 0
    while (a < len(issues)) and (not volume_str in str(issues[a])):
        a += 1
    while (a < len(issues)) and (volume_str in str(issues[a])):
        tag_str = str(issues[a])
        url_start = tag_str.find(volume_str)
        url_end = tag_str.find('.shtml') + 6
        new_link = radical + tag_str[url_start:url_end]
        if new_link not in issues_list:
            issues_list.append(new_link)
        a += 1
    return issues_list



def get_key_words_manu(article_url):
    article_html = requests.get(article_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    meta = soup_article.find('meta', attrs={'name': 'keywords'})
    keywords_tag = str(meta).split(">")[0]
    key_words_set = set(keywords_tag[15:-18].split(","))
    return key_words_set


def get_article_manu(issue_url, years):
    radical = 'http://manu46.magtech.com.cn/Jweb_prai/EN'
    article_str = '/abstract/abstract'
    link_list = []
    year = 0
    html_issue_data  = requests.get(issue_url).text
    soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
    b = soup_issue.find_all('b')
    i = 0
    while str(b[i])[3:12] != "Published":
        i += 1
    year = int(str(b[i])[-8:-4])
    if year >= years[0]:
        for link in soup_issue.find_all('a', href = True):
            if article_str in str(link):
                tag_str = str(link)
                link_start = 22
                link_end = find_nth(tag_str, "\"", 4)
                if tag_str[link_end-8:link_end-6].isdigit():
                    new_link = radical + tag_str[link_start:link_end]
                    if not new_link in link_list:
                        link_list.append(new_link)
    return year, link_list




def get_issue_manu(journal_url):
    radical = 'http://manu46.magtech.com.cn/Jweb_prai/EN/'
    volume_str = 'showTenYearVolumnDetail'
    issue_str = 'volumn/volumn'
    issues_list = []
    html_journal_data  = requests.get(journal_url).text
    soup_journal = BeautifulSoup(html_journal_data, 'html.parser')
    year_issues = soup_journal.find_all('a')
    a = 0
    while (a < len(year_issues)) and (not volume_str in str(year_issues[a])):
        a += 1
    while (a < len(year_issues)) and (volume_str in str(year_issues[a])):
        tag_str = str(year_issues[a])
        year_url_start = tag_str.find(volume_str)
        year_url_end = find_nth(tag_str, '"', 2)
        year_url = radical + "article/" + tag_str[year_url_start:year_url_end]
        html_year_data  = requests.get(year_url).text
        soup_year = BeautifulSoup(html_year_data, 'html.parser')
        issues = soup_year.find_all('a')
        b = 0
        while (b < len(issues)) and (not issue_str in str(issues[b])):
            b += 1
        while (b < len(issues)) and (issue_str in str(issues[b])):
            tag_str = str(issues[b])
            url_start = tag_str.find(issue_str)
            url_end = find_nth(tag_str, '"', 4)
            new_link = radical + tag_str[url_start:url_end]
            if new_link not in issues_list:
                issues_list.append(new_link)
            b += 1
        a += 1
    return issues_list



def get_article_IEEE(issue_url, years):
    link_list = []
    year = 0
    year = int(issue_url[-9:-5])
    if year >= years[0]:
        html_issue_data  = requests.get(issue_url).text
        soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
        for link in soup_issue.find_all('a', href=True):
            if "https://doi.org" in str(link):
                tag_str = str(link)
                if"><" in tag_str:
                    link_start = 9
                    link_end = find_nth(tag_str, "\"", 2)
                    new_link = tag_str[link_start:link_end]
                    if new_link not in link_list:
                        link_list.append(tag_str[link_start:link_end])
    return year, link_list


def get_issue_IEEE(journal_url):
    issues_list = []
    req = Request(journal_url, headers={'User-Agent': 'Mozilla/5.0'})
    article_html = urlopen(req).read()
    soup_issue = BeautifulSoup(article_html, 'html.parser')
    for link in soup_issue.find_all('a', href=True):
        tag_str = str(link)
        if len(tag_str) > 14 and tag_str[-14:len(tag_str)] == '[contents]</a>':
            url_start = tag_str.find("href=") + 6
            url_end = tag_str.find('">')
            new_link = tag_str[url_start:url_end]
            if new_link not in issues_list:
                issues_list.append(new_link)
    return issues_list


def get_key_words_IEEE(article_url):
    """
    This function extracts the keywords from a IEEE article
    """
    key_words_set = set()
    article_html = requests.get(article_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    scripts = soup_article.find_all('script')
    i = 0
    cursor = 0
    while((i < len(scripts)) & (cursor == 0)):
        metadata_str = str(scripts[i]).lower()
        if("keywords" in metadata_str):
            list_start = find_nth(metadata_str, "keywords", 2) + 10
            if("[" in metadata_str[list_start:-1]):
                nested_level = 1
                cursor = list_start + 1
                while nested_level > 0:
                    if metadata_str[cursor] == "[":
                        nested_level += 1
                    elif metadata_str[cursor] == "]":
                        nested_level -= 1
                    cursor += 1
                list_end = cursor
            else:
                i=len(scripts)
        i += 1
    if i < len(scripts):
        keywords_lists = ast.literal_eval(metadata_str[list_start:list_end])
        for l in range(len(keywords_lists)):
            if type(keywords_lists[l]) is dict:
                for k in keywords_lists[l].keys():
                    if type(keywords_lists[l][k]) is list:
                        key_words_set.update(keywords_lists[l][k])
    return key_words_set


def get_key_words_springer(article_url):
    key_words_set = set()
    article_html = requests.get(article_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    scripts = soup_article.find_all('script')
    metadata_str = str(scripts[1]).lower()
    if("kwrd" in metadata_str):
        list_start = metadata_str.find("kwrd") + 7
        list_end = metadata_str[list_start:].find("]") + list_start
        key_words_set = ast.literal_eval("{" + metadata_str[list_start:list_end] + "}")
    return key_words_set


def get_issue_Elsevier(journal_url):
    issues_list = []
    req = Request(journal_url + "issues/", headers={'User-Agent': 'Mozilla/5.0'})
    article_html = urlopen(req).read()
    soup_journal = BeautifulSoup(article_html, 'html.parser')
    links = soup_journal.find_all('a')
    a = 0
    while '/vol/' not in str(links[a]):
        a+=1
    cursor = str(links[a]).find('/vol/')+5
    number_of_digits = 4
    number = str(links[a])[cursor:cursor + number_of_digits]
    while not number.isdigit() and number_of_digits > 0:
        number_of_digits -= 1
        number = str(links[a])[cursor:cursor + number_of_digits]
    if number.isdigit():
        for i in range(int(number),0,-1):
            new_link = journal_url + 'vol/' + str(i) + '/suppl/C'
            if new_link not in issues_list:
                issues_list.append(new_link)
    return issues_list


def get_article_Elsevier(issue_url, years):
    radical = 'https://www.sciencedirect.com'
    article_str = '/science/article/'
    link_list = []
    year = 0
    req = Request(issue_url, headers={'User-Agent': 'Mozilla/5.0'})
    article_html = urlopen(req).read()
    soup_issue = BeautifulSoup(article_html, 'html.parser')
    title_tag = soup_issue.find('title')
    title_str = str(title_tag)
    cursor = title_str.find('| Science') - 5
    if not title_str[cursor:cursor+4].isdigit():
        cursor -=1
    # print(title_str[cursor:cursor+4])
    if title_str[cursor:cursor+4].isdigit():
        year = int(title_str[cursor:cursor+4])
    else:
        year = np.nan
    if year >= years[0]:
        tags = soup_issue.find_all('a')
        for a in tags:
            if article_str in str(a):
                tag_str = str(a)
                link_start = tag_str.find(article_str)
                link_end = find_nth(tag_str, "\"", 4)
                new_link = radical + tag_str[link_start:link_end]
                if new_link[-1].isdigit() and not new_link in link_list:
                    link_list.append(new_link)
    return year, link_list


def get_key_words_Elsevier(article_url):
    """
    This function extracts the keywords from a IEEE article. The previous 
    method does not work, probably because of the use of Javascript in the
    source of the page.
    """
    key_words_set = set()
    req = Request(article_url, headers={'User-Agent': 'Chrome/51.0.2704.103'}) # The format obtained for Firefox is hard to get data from.
    article_html = urlopen(req).read()
    soup_article = BeautifulSoup(article_html, 'html.parser')
    divs = soup_article.find_all("div", attrs={"class" : "keyword"})
    for div in divs:
        tag_str = str(div)
        word_start = find_nth(tag_str, ">", 2) + 1
        word_end = tag_str.find("</span>")
        key_words_set.add(tag_str[word_start:word_end])
    return key_words_set



def get_issue_joig(journal_url):
    issues_list = []
    volume_str = "Volume "
    article_html = requests.get(journal_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    links = soup_article.find_all('a')
    for a in links:
        tag_str = str(a)
        if volume_str in tag_str:
            link_start = 9
            link_end = tag_str.find('">')
            new_link = tag_str[link_start:link_end]
            new_link = new_link.replace('&amp;', '&')
            if new_link[-1].isdigit() and new_link not in issues_list:
                issues_list.append(new_link)
    return issues_list


def get_article_joig(issue_url, years):
    link_list = []
    year = 0
    article_html = requests.get(issue_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    title = soup_article.find("title")
    title_str = str(title)
    cursor = title_str.find("20")
    year_str = title_str[cursor:cursor+4]
    if year_str.isdigit():
        year = int(year_str)
        links = soup_article.find_all("a", attrs={"target" : "_blank"})
        for a in links:
            tag_str = str(a)
            link_start = 9
            link_end = find_nth(tag_str, "\"", 2)
            new_link = tag_str[link_start:link_end]
            new_link = new_link.replace('&amp;', '&')
            if new_link not in link_list:
                link_list.append(new_link)
    return year, link_list


def get_key_words_joig(article_url):
    """
    This function extracts the keywords from a IEEE article. The previous 
    method does not work, probably because of the use of Javascript in the
    source of the page.
    """
    article_html = requests.get(article_url).text
    soup_article = BeautifulSoup(article_html, 'html.parser')
    source = str(soup_article)
    cursor = source.find("<strong>—</strong>")+18
    key_words_end = source[cursor:].find("<br/>")
    key_words_string = source[cursor:cursor+key_words_end]
    key_words_list = key_words_string.split(sep= ", ")
    key_words_set = set(key_words_list)
    return key_words_set


def get_article_dakd(issue_url, years):
    radical = 'https://manu44.magtech.com.cn/Jwk_infotech_wk3/EN/'
    link_list = []
    year = 0
    html_issue_data  = requests.get(issue_url).text
    soup_issue = BeautifulSoup(html_issue_data, 'html.parser')
    span = soup_issue.find("span", attrs={"class" : "abs_njq"})
    cursor = str(span).find('>') + 1
    year_str = str(span)[cursor:cursor+4]
    if year_str.isdigit():
        year = int(year_str)
        if year >= years[0]:
            links = soup_issue.find_all("a", attrs={"target" : "_blank"})
            for a in links:
                tag_str = str(a)
                if radical in tag_str:
                    link_start = tag_str.find("https:")
                    link_end = find_nth(tag_str, '"', 4)
                    new_link = tag_str[link_start:link_end]
                    if new_link not in link_list:
                        link_list.append(new_link)
    return year, link_list


def get_issue_dakd(journal_url):
    radical = 'http://manu44.magtech.com.cn/Jwk_infotech_wk3/EN/'
    issue_str = 'volumn/volumn'
    issues_list = []
    html_journal_data  = requests.get(journal_url).text
    soup_journal = BeautifulSoup(html_journal_data, 'html.parser')
    issues = soup_journal.find_all('a')
    for a in issues:
        tag_str = str(a)
        if issue_str in tag_str:
            link_start = 12
            link_end = find_nth(tag_str, "\"", 2)
            new_link = radical + tag_str[link_start:link_end]
            if new_link[-6:] == '.shtml' and new_link not in issues_list:
                issues_list.append(new_link)
    return issues_list


names = {'west1': 'IEEE Transactions on Pattern Analysis and Machine Intelligence', 
         'west2': 'Expert Systems with Applications',
         'west3': 'IEEE Transactions on Neural Networks and Learning Systems', 
         'west4': 'Journal of Machine Learning Research',
         'west5': 'Pattern Recognition', 
         'west6': 'IEEE Transactions on Fuzzy Systems', 
         'west7': 'International Journal of Computer Vision', 
         'west8': 'Information Sciences',
         'west9': 'Proceedings - IEEE International Conference on Robotics and Automation',
         'china1': 'Kongzhi yu Juece/Control and Decision', 
         'china2': 'Jiqiren/Robot', 
         'china3': 'Moshi Shibie yu Rengong Zhineng/Pattern Recognition and Artificial Intelligence', 
         'china4': 'Big Data Mining and Analytics', 
         'china5': 'Computational Visual Media',
         'china6': 'Information and Control', 
         'china7': 'Artificial Intelligence in Agriculture',
         'china8': 'Journal of Image and Graphics',
         'china9': 'Data Analysis and Knowledge Discovery'
         }


url = {'west1': 'https://dblp.org/db/journals/pami/index.html', 
       'west2': 'https://www.sciencedirect.com/journal/expert-systems-with-applications/', #'https://dblp.org/db/journals/eswa/index.html',
       'west3': 'https://dblp.org/db/journals/tnn/index.html', 
       'west4': 'https://dblp.org/db/journals/jmlr/index.html', 
       'west5': 'https://www.sciencedirect.com/journal/pattern-recognition', #'https://dblp.org/db/journals/pr/index.html', 
       'west6': 'https://dblp.org/db/journals/tfs/index.html', 
       'west7': 'https://dblp.org/db/journals/ijcv/index.html', 
       'west8': 'https://www.sciencedirect.com/journal/information-sciences/' , #'https://dblp.org/db/journals/isci/index.html', 
       'west9': 'https://dblp.org/db/conf/icra/index.html', 
       'china1': 'https://navi.cnki.net/knavi/journals/KZYC/detail?uniplatform=NZKPT', 
       'china2': 'http://robot.sia.cn/EN/article/showOldVolumn.do', 
       'china3': 'http://manu46.magtech.com.cn/Jweb_prai/EN/article/showTenYearOldVolumn.do', 
       'china4': 'https://dblp.org/db/journals/bigdatama/index.html', 
       'china5': 'https://dblp.org/db/journals/cvm/index.html',
       'china6': 'http://xk.sia.cn/CN/article/showTenYearOldVolumn.do', 
       'china7': 'https://www.sciencedirect.com/journal/artificial-intelligence-in-agriculture/',
       'china8': 'http://www.joig.net/index.php?m=content&c=index&a=lists&catid=9',
       'china9': 'https://manu44.magtech.com.cn/Jwk_infotech_wk3/EN/2096-3467/home.shtml'}


journal_scraper = {'west1': (get_issue_dblp, get_article_dblp, get_key_words_IEEE), 
                  'west2': (get_issue_Elsevier, get_article_Elsevier, get_key_words_Elsevier), 
                  'west3': (get_issue_dblp, get_article_dblp, get_key_words_IEEE), 
                  'west4': (get_issue_dblp, get_article_dblp, 'tbd'), 
                  'west5': (get_issue_Elsevier, get_article_Elsevier, get_key_words_Elsevier), 
                  'west6': (get_issue_dblp, get_article_dblp, get_key_words_IEEE), 
                  'west7': (get_issue_dblp, get_article_dblp, np.nan), 
                  'west8': (get_issue_dblp, get_article_dblp, get_key_words_Elsevier), 
                  'west9': (get_issue_IEEE, get_article_IEEE, get_key_words_springer),#, get_key_words_IEEE), 
                  'china1': ('tbd','tbd','tbd'), 
                  'china2': (get_issue_jiqiren, get_article_jiqiren, get_key_words_manu), 
                  'china3': (get_issue_manu, get_article_manu, get_key_words_manu),
                  'china4': (get_issue_dblp, get_article_dblp, get_key_words_IEEE), 
                  'china5': (get_issue_dblp, get_article_dblp, np.nan), 
                  'china6': (get_issue_manu, get_article_manu, get_key_words_manu),
                  'china7': (get_issue_Elsevier, get_article_Elsevier, get_key_words_Elsevier), 
                  'china8': (get_issue_joig, get_article_joig, get_key_words_joig), 
                  'china9': (get_issue_dakd, get_article_dakd, get_key_words_manu)}

journals_table = pd.DataFrame(columns=['names', 'journal url', 'journal scraper'])
for j in jidx:
    journals_table.loc[j,'names'] = names[j]
    journals_table.loc[j,'journal url'] = url[j]
    journals_table.loc[j,'journal scraper'] = journal_scraper[j]



years = list(range(2010,date.today().year+1))
china_keywords = pd.DataFrame(columns=years)
west_keywords = pd.DataFrame(columns=years)


pickle_file = "ChinavsWest.p"
west_csv_file = "West keywords.csv"
china_csv_file = "China keywords.csv"
column_names = ['index', 'journal' , 'issue', 'article', 'keywords', 'year']

if os.path.exists(pickle_file):
    db = pickle.load(open(pickle_file, "rb"))
else:
    db = pd.DataFrame(columns=column_names)



# If the database of journal articles is not filled yet, it is loaded there.
if (len(db) == 0) or (db.iloc[-1,0][0] != jidx[journals_nb]):
    # Getting the url of all the papers in AI:
    for j in range(journals_nb+1):
        print(jidx[j])
        year = date.today().year
        i = 0
        issues_list = journals_table.loc[jidx[j],'journal scraper'][0](journals_table.loc[jidx[j],'journal url'])
        while year >= years[0] and i< len(issues_list):
            year, link_list = journals_table.loc[jidx[j],'journal scraper'][1](issues_list[i], years)
            print(year)
            if year >= years[0]:
                idx = [[jidx[j], i, x] for x in list(range(len(link_list)))]
                issue_df = pd.DataFrame({"index": idx, 
                                         "year": year, 
                                         "journal": journals_table.loc[jidx[j],'journal url'], 
                                         "issue": issues_list[i], 
                                         "article": list(link_list), 
                                         "keywords": np.nan})
                db = pd.concat([db,issue_df])
            elif year!= year: # We exit the loop when we reach an old issue. NaN's are for issues with a different formatting; we ignore them and continue
                year = date.today().year
            i += 1
    pickle.dump(db, open(pickle_file,"wb"))


# Extracting the key words. This is done on the journal website, and
# thus requires a different method depending on the journal.

for row in range(len(db)):
    print(db.loc[row,'index'][0], row)
    key = db.loc[row,'index'][0]
    article_url = db.loc[row,'article']
    year = int(db.loc[row,'year'])
    key_words_set = journals_table.loc[key,'journal scraper'][2](article_url)
    db.at[row,"keywords"] = key_words_set
    for word in key_words_set:
        word = word.lower()
        if key[0:4] == 'west':
            if not (word in west_keywords.index):
                word_df = pd.DataFrame([[0]*west_keywords.shape[1]],columns=west_keywords.columns, index = [word])
                west_keywords = pd.concat([west_keywords,word_df])
            west_keywords.loc[word,year] += 1
        else:
            if not (word in china_keywords.index):
                word_df = pd.DataFrame([[0]*china_keywords.shape[1]],columns=china_keywords.columns, index = [word])
                china_keywords = pd.concat([china_keywords,word_df])
            china_keywords.loc[word,year] += 1


# Identifying themes:
vision = set()
robot = set()
deep_learning = set()
fuzzy = set()
learning = set()
speech = set()
NLP = set()
data = set()
decision = set()
dictionaries = [west_keywords.index, china_keywords.index]
for dico in dictionaries:
    vision = vocabulary(vision,"image",dico)
    vision = vocabulary(vision,"vision",dico)
    robot = vocabulary(robot,"robot",dico)
    deep_learning = vocabulary(deep_learning,"neur",dico)
    fuzzy = vocabulary(fuzzy,"fuzzy",dico)
    learning = vocabulary(learning,"learn",dico)
    speech = vocabulary(speech,"speech",dico)
    speech = vocabulary(speech,"voice",dico)
    NLP = vocabulary(NLP,"lang",dico)
    NLP = vocabulary(NLP,"word",dico)
    NLP = vocabulary(NLP,"ling",dico)
    NLP = vocabulary(NLP,"vocabulary",dico)
    data = vocabulary(data,"data",dico)
    decision = vocabulary(decision,"decision",dico)

topic_dict = {"vision": vision, "robot":robot, "deep learning": deep_learning, "fuzzy logic": fuzzy, "learning": learning, "speech": speech, "NLP": NLP, "data":data, "decision":decision}
west_graph_data = pd.DataFrame(0, index=topic_dict.keys(), columns=years)
china_graph_data = pd.DataFrame(0, index=topic_dict.keys(), columns=years)
for topic in topic_dict:
    for word in topic_dict[topic]:
        if word in west_keywords.index:
            for year in years:
                west_graph_data.at[topic,year] += west_keywords.at[word,year]
        if word in china_keywords.index:
            for year in years:
                china_graph_data.at[topic,year] += china_keywords.at[word,year]

multiplier = round(sum(west_graph_data.sum())/sum(china_graph_data.sum()))
for p in topic_dict:
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot(west_graph_data.columns, west_graph_data.loc[p,:], 'b', china_graph_data.columns, china_graph_data.loc[p,:]*multiplier, 'r')
    plt.xlabel('year')
    plt.ylabel('Number of papers published (times ' + str(multiplier) + " for China)")
    plt.title(p)