import logging
import random
from flask import current_app
from urllib.parse import quote
from .lagou import Crawler_for_Lagou
from .liepin import Crawler_for_Liepin
from .qiancheng import Crawler_for_51job
from ..model import db, Ip_pool
from .proxy_ip import GetIps

#约定：发布时间选项为：None, 24  72
#约定：工资有None, ‘3K以下’，‘3k-6k’，‘6k-10k’，‘10k以上’
#约定：经验要求：None,‘无要求’，‘1-3年’，‘3年以上’

class CrawlerHandler():

	def __init__(self, keyword, exp=None, edu=None, page=1,
				city='成都', salary=None, pub_time=None):
		self.keyword = keyword
		self.exp = exp
		self.edu = edu
		self.city = city
		self.salary = salary
		self.page = page
		self.pub_time = pub_time

	def QianChengLinkGenerator(self):
		'''generate the url with the parameters and 
			return a instance of the 51job crawler
		'''
		if self.city == '成都':
			city_code = '090200'
			area_code = '090200'
		if self.pub_time is None:
			pub_time_code = 9
		elif self.pub_time == '24':
			pub_time_code = 0
		elif self.pub_time == '72':
			pub_time_code = 1
		if self.salary is None:
			salary_code = 99
		keyword_code = quote(self.keyword)
		page_code = self.page
		if self.exp is None:
			exp_code = None
		elif self.exp == '无要求':
			exp_code = '01'
		elif self.exp == '1-3年':
			exp_code = '02'
		elif self.exp == '3年以上':
			exp_code = '03'
		link =  'http://search.51job.com/list/%s,%s,0000,00,%s,%s,%s,2,%s.html?workyear=%s'%(
				city_code, area_code, pub_time_code,salary_code, keyword_code, page_code,
				 exp_code)
		print ('link is:',link)
		logging.info('Searching QC MAIN: key: %s, link: %s'%(self.keyword, link))
		return Crawler_for_51job(link, self.get_10_proxies('qc'))


	def liepinLinkGenerator(self):
		'''generate the url with the parameters and 
			return a instance of the liepin crawler
		'''
		keyword_code = quote(self.keyword)
		if self.city == '成都':
			city_code = 280020
		if self.pub_time is None:
			pub_time_code = None      #quote(pub_time)
		elif self.pub_time == '24':
			pub_time_code = 1
		elif self.pub_time == '72':
			pub_time_code = 3
		if self.salary is None:
			salary_code = None
		page_code = self.page
		link = 'https://www.liepin.com/zhaopin/?key=%s&dqs=%s&pubTime=%s&salary=%s&curPage=%s'%(keyword_code, \
				city_code, pub_time_code, salary_code, page_code)
		print ('main link is:', link)
		logging.info('Searching LP MAIN MAIN: key: %s, link: %s'%(self.keyword, link))
		return Crawler_for_Liepin(link, self.get_10_proxies('lp'))

	def lagouLinkGenerator(self):
		'''generate the url with the parameters and 
			return a instance of the lagou crawler
		'''
		city_code = quote(self.city)
		page = self.page
		keyword = self.keyword
		link = 'https://www.lagou.com/jobs/positionAjax.json?city=%s&needAddtionalResult=false&isSchoolJob=0'%city_code
		logging.info('Searching LG MAIN: key: %s, link: %s'%(keyword, link))
		return Crawler_for_Lagou(link, page, keyword, self.get_10_proxies('lg'))

	def __user_agent_resources(self):
		#user_agent list
		user_agents = ['Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) \
				AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
			'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 \
				(KHTML, like Gecko) Version/5.1 Safari/534.50',
			'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
			'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
			'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
			'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
			'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
			'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
			'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
			'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 \
				(KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Maxthon 2.0)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; \
				SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
			'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
			]
		return random.choices(user_agents, k=30)

	def update_ip(self):
		print ('--searching the proxy ip--')
		search_proxy = GetIps()
		search_proxy.fresh_ip()
		print ('--searching ends--')

	def __proxy_resources(self, site):
		'''input: 'qc' or 'lg' or 'lp' corresponding to each website
		get 10 proxy ip addresses from database
		return: a list of proxy ip addresses
		'''
		with current_app.app_context():
			if site == 'qc':
				ip_obj = Ip_pool.query.filter_by(qc_status=True).all()
				print ('----qc-%s-----'%(len(ip_obj)))
				if len(ip_obj) < 30:
					self.update_ip()
					ip_obj = Ip_pool.query.filter_by(qc_status=True).all()
			elif site == 'lg':
				ip_obj = Ip_pool.query.filter_by(lg_status=True).all()
				print ('----lg-%s-----'%(len(ip_obj)))
				if len(ip_obj) < 30:
					self.update_ip()
					ip_obj = Ip_pool.query.filter_by(qc_status=True).all()
			elif site == 'lp':
				ip_obj = Ip_pool.query.filter_by(lp_status=True).all()
				print ('----lp-%s-----'%(len(ip_obj)))
				if len(ip_obj) < 30:
					self.update_ip()
					ip_obj = Ip_pool.query.filter_by(qc_status=True).all()
			else:
				return None

			twenty_ip = random.sample(ip_obj, 30)
			#return [{i.scheme : 'http://'+i.ip+':'+i.port} for i in twenty_ip]
			return [{i.scheme : 'http://'+i.ip+':'+i.port} for i in twenty_ip] #{'http':'http://'}

	def get_10_proxies(self, site):
		#input: 'qc' or 'lg' or 'lp' corresponding to each website
		#return 10 proxy addresses, each one was attached with a user_agent
		return list(zip(self.__user_agent_resources(), self.__proxy_resources(site)))
