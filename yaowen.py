# -*- coding:utf8 -*-
"""要闻抓取自动发布程序
@module:NMGywMain
@author:Derek.S
@runtime:Python 2.x
@Version:1.2
2017-11-07
"""


import urllib2
import re
from bs4 import BeautifulSoup
import sqlite3
from selenium import webdriver
import time
import sys
from colorama import Fore
import random

db = sqlite3.connect("db.db")
c = db.cursor()
Version = '1.2 防爬虫检测版 2017-11-07'

# db.set_character_set('utf8')
# 2017-11-07 新增


def TitleCheck(titie):
    """新增代码，检测网页标题是否为防御"""
    if titie == u"365GCD云防御":
        print '云防御页面，等待120s后重新抓取'
        time.sleep(120)
        return 'error'
    else:
        return 'ok'


Request_Headers = {
    "Referer":
    "http://www.nmg.gov.cn/fabu/xwdt/nmg/",
    "User-Agent":
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}


def PageNumber():
    """页码获取"""
    NmGovPage = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/index.html'
    Request = urllib2.Request(NmGovPage, headers=Request_Headers)
    PageSC = urllib2.urlopen(Request).read()
    PNSoup = BeautifulSoup(PageSC, "html.parser")
    if TitleCheck(PNSoup.title.get_text()) == 'error':
        return 'error'
    PageNSC = PNSoup.find('div', class_="pages")
    ReCountPage = r"var countPage\s.\s.\d*"
    PageN = re.search(ReCountPage, PageNSC.get_text())
    RePageNumber = r"\d+"
    CountPage = re.search(RePageNumber, PageN.group()).group()
    return CountPage


def YWList(number):
    """列表页获取li URL"""
    if ((number - 1) == 0):
        NmGovUrl = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/index.html'
        YWListProc(NmGovUrl)
    elif (number != 0):
        ListPageNumber = number - 1
        NmGovUrlNext = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/index_' + str(
            ListPageNumber) + '.html'
        YWListProc(NmGovUrlNext)
    else:
        PageI = 0
        if PageNumber() == "error":
            G365 = True
            while G365:
                if PageNumber() == 'error':
                    pass
                else:
                    CountPageN = PageNumber()
                    G365 = False
        else:
            CountPageN = PageNumber()
            while (PageI < int(CountPageN)):
                if PageI == 0:
                    NmGovUrl = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/index.html'
                    YWListProc(NmGovUrl)
                else:
                    ListPageNumber = PageI
                    NmGovUrlNext = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/index_' + str(
                        ListPageNumber) + '.html'
                    YWListProc(NmGovUrlNext)
                PageI += 1
    print Fore.YELLOW + '采集自治区要闻完成，返回主菜单。'
    print Fore.WHITE + ''
    MainMenu()


def YWListProc(url):
    """检测并采集文章"""
    Url = 'http://www.nmg.gov.cn/fabu/xwdt/nmg/'
    Url365 = url
    Request = urllib2.Request(url, headers=Request_Headers)
    PageContent = urllib2.urlopen(Request).read()
    Soup = BeautifulSoup(PageContent, "html.parser")
    Title = Soup.title.get_text()
    if Title == u"365GCD云防御":
        print '检测到云防御，等待300s'
        time.sleep(300)
        YWListProc(Url365)
    else:
        List = Soup.find_all('ul')
        LiList = List[1].find_all(['li'])
        # print LiList
        for a in LiList:
            NewsUrl = a.a.get('href')
            NewsTitle = a.a.get_text()
            NewsTItleT = [(NewsTitle)]
            NewsOrigin = a.find_all('span', class_="laiyuan")[0].get_text()[3:]
            NewsDate = a.find_all('span', class_="date")[0].get_text().strip()
            c.execute('select Title from NewsContent where Title = ?',
                      (NewsTItleT))
            TitleCheck = c.fetchone()
            if (TitleCheck == None):
                print NewsUrl.replace('./',
                                      Url), NewsTitle, NewsOrigin, NewsDate
                News(
                    NewsUrl.replace('./', Url), NewsTitle, NewsOrigin,
                    NewsDate)
                # News("http://www.nmg.gov.cn/fabu/xwdt/nmg/201703/t20170323_604342.html",NewsTitle,NewsOrigin,NewsDate)
            else:
                print Fore.RED + NewsTitle + u' 该文章已存在，跳过抓取'
                print Fore.WHITE + ''


def News(url, title, origin, date):
    """采集文章详情页"""
    try:
        Request = urllib2.Request(url, headers=Request_Headers)
        NewsContentSC = urllib2.urlopen(Request).read()
        NewsSoup = BeautifulSoup(NewsContentSC, "html.parser")
        # 防御检测
        if NewsSoup.title.get_text() == u"365GCD云防御":
            print '检测到云防御，等待300s'
            time.sleep(300)
            News(url, title, origin, date)
        else:
            NewsContent = NewsSoup.find_all('div', class_="content")
            if (NewsContent[0].find_all('style') != None):
                NewsTextSC = NewsContent[0].find_all('style')
                Rep = r"<!--\s*.*\s*.*\s*\s*.*\s*.*\s*.\s*.*\s*.\s*.*\s*.\s*//-->"
                for sytle in NewsTextSC:
                    sytle.clear()
            NewsText = re.sub(Rep, '', NewsContent[0].get_text()).strip()
            # print NewsText
            print "写入数据库"
            DBInto = [(title, str(url), origin, date, NewsText)]
            c.execute(
                "insert into NewsContent(Title,URL,Origin,Date,Content)  values(?,?,?,?,?)",
                (DBInto[0]))
            # print ("insert into NewsContent(Title,URL,Origin,Date,Content)  values( '%s', '%s', '%s', '%s','%s')" % (title,str(url),origin,date,NewsText))
            db.commit()
            # 2017.11.17 更新随机等待时间
            a = random.randint(15, 180)
            print "数据库写入完毕，防爬虫检测，等待 %d" % a
            time.sleep(a)
    except BaseException, e:
        print 'error'
        print e
        pass
    else:
        pass


def AutoPublish(NewsID, TitleText, NewsPText, CopyFrom, CopyURL, NewsDate):
    """自动发布模块
    NewsID:新闻ID
    TitleText:标题文字
    NewsPText:新闻内容
    CopyFrom:转载自
    CopyURL:转载URL
    NewsDate:新闻发布时间"""
    print '等待跳转……'
    time.sleep(10)
    print '定位页面……'
    Window = driver.current_window_handle
    print u"跳转到发布自治区转载页面"
    driver.get(
        "http://user.a.cn/index.php?c=content&m=create&selected_channel=581aa921ceab06d64e5db645"
    )
    time.sleep(10)
    NowHandle = driver.current_window_handle  # 获取常规内容创建页面句柄
    print "展开更多设置……"
    driver.find_element_by_id("advSearch").click()
    print "填充内容……"
    DataTitle = driver.find_element_by_name("data[title]")
    # TitleText = u"测试标题2333"
    DataTitle.click()
    DataTitle.send_keys(TitleText)
    DataTitle.click()
    driver.find_element_by_name("data[thumb_name]").click()
    driver.switch_to_default_content()
    time.sleep(5)
    ErrorTitle = driver.find_element_by_xpath(
        ".//*[@id='duplicate_status_span']/img").get_attribute("src")
    if (ErrorTitle == "http://user.a.cn/media/images/error.gif"):
        print Fore.RED + '标题重复，跳过'
        print 'ID写入已发布表'
        c.execute("insert into IDList(NewsID) values('%s')" % (str(NewsID)))
        db.commit()
        print Fore.WHITE + ''
        driver.quit()
    else:
        Tinymce = driver.find_element_by_id("editor_message_ifr")
        driver.switch_to.frame(Tinymce)
        TinymceP = driver.find_element_by_id("tinymce")
        # NewsPText = u"测试自动填充内容"
        TinymceP.send_keys(NewsPText)
        driver.switch_to_default_content()
        driver.find_element_by_id("mce_51").click()
        time.sleep(5)
        driver.switch_to_default_content()
        driver.find_element_by_xpath(
            "/html/body/div[last()-1]/div[last()]/div[1]/div[last()]/button"
        ).click()
        # clean Date
        driver.execute_script(
            "document.getElementsByName('data[release_date]')[0].value=''")
        NewsTime = NewsDate + " 10:00:00"
        driver.find_element_by_name("data[release_date]").send_keys(NewsTime)
        driver.find_element_by_name("data[tag]").click()
        # CopyFrom = u"测试来源"
        driver.find_element_by_name("data[copy_from]").send_keys(CopyFrom)
        # CopyURL = "http://www.test.com"
        driver.find_element_by_name("data[copysource_url]").send_keys(CopyURL)
        driver.execute_script(
            "document.getElementsByName('data[author]')[0].value=''")
        Author = driver.find_element_by_id("author")
        Author.find_element_by_xpath("//option[@value='']").click()
        driver.execute_script(
            "document.getElementsByName('save_author')[0].checked=false")
        driver.find_element_by_id("advSearch").click()
        print "修改审核状态……"
        Status = driver.find_element_by_name("data[status]")
        Status.find_element_by_xpath("//option[@value='1']").click()
        Save = driver.find_element_by_name("submit_btn")
        print "正在发布……"
        Save.click()
        print 'ID写入已发布表'
        c.execute("insert into IDList(NewsID) values('%s')" % (str(NewsID)))
        db.commit()
        print Fore.BLUE + '发布完成，准备开始下一条。'
        print Fore.WHITE + ''
        time.sleep(10)


def SelectNews(date):
    """检索数据库内新闻，启动Selenium"""
    print '将' + str(date) + '的要闻自动发布'
    print '启动Driver'
    global driver
    # driver = webdriver.Chrome(executable_path='/home/dereks/chromedriver')
    driver = webdriver.Chrome(executable_path='lib/chromedriver')
    driver.get("url") # 后台地址
    UserName = '' # 用户名
    PassWord = '' # 密码
    LoginFormName = driver.find_element_by_id("email")
    LoginFormName.send_keys(UserName)
    LoginFormPass = driver.find_element_by_id("password")
    LoginFormPass.send_keys(PassWord)
    print '请输入验证码，等待30s'
    time.sleep(30)
    c.execute('select * from NewsContent where Date = "%s"' % (str(date)))
    DBNews = c.fetchall()
    DBNewsLength = len(DBNews)
    DBi = 0
    while (DBi < DBNewsLength):
        DBSID = DBNews[DBi][0]
        DBSTitle = DBNews[DBi][1]
        DBSURL = DBNews[DBi][2]
        DBSOrigin = DBNews[DBi][3]
        DBSDate = DBNews[DBi][4]
        DBSContent = DBNews[DBi][5]
        c.execute('select NewsID from IDList where NewsID = "%s"' %
                  (str(DBSID)))
        IDCheck = c.fetchone()
        if (IDCheck == None):
            AutoPublish(DBSID, DBSTitle, DBSContent, DBSOrigin, DBSURL,
                        DBSDate)
            DBi += 1
        else:
            print Fore.RED + u'ID：' + IDCheck[0] + u' ID已用表内查询到文章ID，跳过发布。'
            print Fore.WHITE + ''
            DBi += 1


def DelDBIDList():
    """清空ID已用表"""
    c.execute('delete from IDList')
    db.commit()
    # c.execute('select * from IDList')
    # test1 = c.fetchall()
    # print test1
    print 'ID已用表已经清空'


def MainMenu():
    """菜单界面"""
    print '--------------------------------------------------'
    print '------      自治区转载自动抓取发布程序      ------'
    print '----  当前版本：' + Version + '   ----'
    print '--------------------------------------------------'
    print '-- 1 抓取数据入库'
    print '-- 2 自动发布转载'
    print '-- 3 清空已用ID表'
    print '-- Q 退出程序'
    print '--------------------------------------------------'
    control = raw_input('-- 请选择你要进行的操作：')
    if (control == '1'):
        PN = PageNumber()
        print u"新闻共计 %s 页" % (PN)
        Number = input('输入要抓取的页码，若需要抓取最新一页，请输入1，抓取全部页面，请输入0：')
        YWList(Number)
    elif (control == '2'):
        print '本功能所需输入的时间为自治区网站要闻发布时间。'
        print '若要转载自治区网站 2017年3月25日 发布的要闻，请输入 2017-03-25'
        print '本程序会根据自治区网站要闻发布时间进行同步操作。'
        AutoDate = raw_input('请输入日期：')
        SelectNews(AutoDate)
        # 关闭driver及数据库链接
        driver.close()
        c.close()
        print Fore.YELLOW + '自动发布完成，关闭Driver，返回主菜单'
        print Fore.WHITE + ''
        MainMenu()
        # AutoPublish()
    elif (control == '3'):
        DelDBIDList()
        MainMenu()
    elif (str(control) == 'Q' or str(control) == 'q'):
        print '-------------------- bye -------------------------'
        sys.exit()


if __name__ == '__main__':
    # YWList()
    MainMenu()
