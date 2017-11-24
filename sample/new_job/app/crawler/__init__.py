
from celery import Task

class MyBase(Task):
	def on_success(self, retval, task_id, args, kwargs):
		#在任务结束时更改时间




class Format():
	#公共类，负责将直接从网页上抓取的内容进行格式化并存储！
	def pub_time_format(self, pub_time):
		'''transfer the time informations which in different type into a 
			common format to store, 5 kinds of time format are acceptable:
			['08-05发布','2017-08-04 22:15:00','15小时前','昨天',8-5，
			'前天','2017-07-30']
		'''
		if '发布' in pub_time:
			str_date = re.search('\d*-\d*',pub_time).group(0)
			return datetime.strptime(str_date, '%m-%d').replace(datetime.now().year)
		elif bool(re.match('\d*-\d*$', pub_time)):
			return datetime.strptime(pub_time, '%m-%d').replace(datetime.now().year)
		elif bool(re.search('前', pub_time)):
			if bool(re.match('^\d{1,2}小时', pub_time)):
				hours = int(re.search('^\d{1,2}', pub_time).group(0))
				return datetime.now()-timedelta(hours=hours)
			elif bool(re.match('^\d{1,2}天', pub_time)):
				days = int(re.search('^\d', pub_time).group(0))
				return datetime.now()-timedelta(days=days)
		elif '刚' in pub_time:
			return datetime.now()
		elif pub_time == '昨天':
			return datetime.now()-timedelta(days=1)
		elif pub_time == '前天':
			return datetime.now()-timedelta(days=2)
		else:
			try:
				return datetime.strptime(pub_time, '%Y-%m-%d')
			except ValueError:
				return datetime.strptime(pub_time, '%Y-%m-%d %H:%M:%S')

	def salary_format(self, salary):
		'''formate the salary information , accepted:
			['0.4-1万/月', '0.4-1千/月', '10K-15K','13-23万''面议']
		'''
		print ('-------%s-----'%salary)
		if not bool(re.search('\d', salary)):
			return 	[0,0]
		elif '万' in salary:
			salary_floor = salary.split('万')[0].split('-')[0]
			salary_ceil = salary.split('万')[0].split('-')[1]
			return [float(salary_floor)*10000, float(salary_ceil)*10000]
		elif '千' in salary:
			salary_floor = salary.split('千')[0].split('-')[0]
			salary_ceil = salary.split('千')[0].split('-')[1]
			return [float(salary_floor)*1000, float(salary_ceil)*1000]
		elif 'K' in salary:
			salary_floor = salary.split('-')[0].split('K')[0]
			salary_ceil = salary.split('-')[1].split('K')[0]
			return [float(salary_floor)*1000, float(salary_ceil)*1000]
		elif 'k' in salary:
			salary_floor = salary.split('-')[0].split('k')[0]
			salary_ceil = salary.split('-')[1].split('k')[0]
			return [float(salary_floor)*1000, float(salary_ceil)*1000]
		else:
			return [0,0]

	def exp_format(self, exp):
		'''fetch the lowest work experience requirement of the job,
			in database there should be two exp column, one store the
			origin requirement, another store the lowest requirment in
			int format so we can sort it conveniently
		'''
		if exp is None:
			return 0
		elif bool(re.search('\d', exp)) is False:
			return 0
		return int(re.search('\d{1,2}',exp).group(0))

	def info_check(self, salary, comp_name, j_name, job_time):
		'''check whether the job has alrady been stored, if yes then break
		and stop the crawler cause that means we have fetch all the newly
		posted job. 
		but jobs that have the sanme name, same company name, 
		and same salary but different pub time with someone which already 
		exists in the database will only add its link into Jobsite table
		cause it's a repeated job.
		others will be normally stored
		'''
		
		check = Jobbrief.query.filter_by(job_name=j_name, 
					job_salary_low=salary[0], job_salary_high=salary[1]
					).join(Jobbrief.company).filter_by(
					company_name=comp_name)
		if check.first() is None:
			return 'new_job'
			
		elif Jobbrief.query.filter_by(job_name=j_name, job_time=job_time,
					job_salary_low=salary[0], job_salary_high=salary[1]
					).join(Jobbrief.company).filter_by(
					company_name=comp_name).first():
			return 'end'
		
		else:
			return 'repeated job'

	def save_company(self,company_name):
		'''if the company is new to us,save it
		'''
		company = Company.query.filter_by(company_name=company_name).first()
		if company is None:
			comp = Company(company_name=jobinfo['company_name'],
							company_site=jobinfo['company_site'])
			comp._save()

	def save_site(self, jid, link):
		job_site = Jobsite(site=link, brief_id=jid)
		job_site._save()	

	def save_job(self, jobinfo):
		new_job = Jobbrief(key_word=self.keyword, 
						job_name=jobinfo['job_name'],
						job_location=jobinfo.get('job_location'), 
						job_salary_low=jobinfo['salary'][0],
						job_salary_high=jobinfo['salary'][1],
						#job_exp=self.exp_format(jobinfo['exp']),
						job_edu=jobinfo.get('edu'),
						job_quantity=jobinfo.get('quantity'),
						job_time=jobinfo['pub_time'],
						job_other_require=jobinfo.get('other_requirement'),
						job_labels=',\n'.join(jobinfo.get('job_labels')) if \
										jobinfo.get('job_labels') is not None else None,
						company=jobinfo['company_name'],
						job_exp = exp_format(jobinfo.get('exp'))
						)
		return new_job._save()


	def save_raw_info(self, job_infos):
		'''just write the raw information about the job into database
		param:
			job_infos: a list containing many dicts, each dict 
				represents a job
		return a list containing many dicts, each dict represents a
			job's information including 'id','exp','job_site'
		'''
		jobinfo['salary'] = self.salary_format(jobinfo['salary'])
		jobinfo['pub_time'] = self.pub_time_format(jobinfo['pub_time'])

		check = self.info_check(formatted_salary, jobinfo['company_name'],
									jobinfo['job_name'], formatted_pub_time)	
		if check == 'end':
			#no more new job, stop searching
			return True
		elif check == 'repeated job':
			#this is a repeated job, so just save the website
			job_id = Jobbrief.query.filter_by(job_name=jobinfo['job_name'], 
				job_salary_low=formatted_salary[0], job_salary_high=formatted_salary[1]).\
				join(Jobbrief.company).filter_by(company_name=jobinfo['company_name']).\
				first().id
			site = Jobsite(brief_id=int(job_id), site=jobinfo['link'])
			self.save(site)
			return False
		elif check == 'new_job':
			#new job, save it!
			#job_dict = {}
			self.save_company(jobinfo['company_name'])
			job_id = self.save_job(jobinfo)
			self.save_site(job_id, jobinfo['link'])
			return False

