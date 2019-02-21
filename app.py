from collections import defaultdict, Counter
import datetime
import psycopg2
import pandas as pd
import calendar
import os
from matplotlib import rcParams
from flask import Flask, render_template, url_for

app = Flask(__name__)

def create_plots():
	for interval in ['day','week','month']:
		cmd = "SELECT project_id, created_at FROM podcasts ORDER BY created_at DESC LIMIT 90000;"
		address = os.environ.get('SPKT_DB')
		conn = psycopg2.connect(address, sslmode='require')
		cur = conn.cursor()
		cur.execute(cmd)
		results = cur.fetchall()
		conn.close()

		cmd = "SELECT title, id FROM projects ORDER BY created_at;"
		address = 'postgres://u136kfhpq99ma7:p625fb4aa54d09cc85052c41d4cd1e712458b1ff00dd12cb6554cd92e136fe604@ec2-52-50-161-37.eu-west-1.compute.amazonaws.com:5432/d5icaceckkld4r'
		conn = psycopg2.connect(address, sslmode='require')
		cur = conn.cursor()
		cur.execute(cmd)
		projects = cur.fetchall()
		conn.close()

		if interval == 'week':
			results = results[:40000]
		if interval == 'day':
			results = results[:15000]

		project_dict = {pair[1]:pair[0] for pair in projects}

		blacklist = [843,1037,1041,1384,1427,1358,756,1385,1370,1042,877,829,828,919,918,917,916,914,913,912,910,908,873]
		days = defaultdict(list)

		for result in results:
			if result[0] not in blacklist:
				if interval == 'week':
					n_common = 7
					days['{}'.format(result[1].isocalendar()[1])] += [result[0]]
				if interval == 'month':
					n_common = 10
					days['{}'.format(result[1].month)] += [result[0]]
				if interval == 'day':
					n_common = 5
					days['{}/{}'.format(result[1].day, result[1].month)] += [result[0]]

		days = {k: days[k] for k in list(days)[:-1]}

		cnt = Counter()
		data = {}
		for day, podcasts in days.items():
			top10 = Counter(podcasts).most_common(n_common)
			top10_title = [(project_dict[pair[0]], pair[1]) for pair in top10] + [('Other', len(podcasts) - sum([pair[1] for pair in top10]))]  
			data[day] = top10_title
		data

		cols = ['Other']
		for day, v in data.items():
			for pair in v:
				if pair[0] not in cols:
					if pair[0] != 'Other':
						cols.append(pair[0][:20])

		d = {}
		for publisher in cols:
			l = []
			# lets get a list of the first publishers counts every day
			for day, values in data.items():
				publishers_that_day = {p[0]:p[1] for p in values}
				if publisher in publishers_that_day:
					l.append(publishers_that_day[publisher])
				else:
					l.append(0)
			d[publisher] = l   

		df = pd.DataFrame(d)
		rcParams.update({'font.size': 16})
		plot = df.plot(kind='bar', stacked=True, rot=0, colormap='tab20c',zorder=3)
		plot.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))

		if interval == 'week':
			plot.set_title('Articles per week')
			ticklabels = ['Week {}\n({})'.format(w, len(v)) for w, v in days.items()]
		if interval == 'month':
			plot.set_title('Articles per month')
			ticklabels = ['{}\n({})'.format(calendar.month_name[int(w)], len(v)) for w, v in days.items()]
		if interval == 'day':
			plot.set_title('Articles per day')
			ticklabels = ['{}\n({})'.format(w, len(v)) for w, v in days.items()]

		plot.set_xticklabels(ticklabels)
		fig = plot.get_figure()
		fig.set_size_inches(18, 10)
		fig.savefig("static/{}.png".format(interval), bbox_inches='tight')


@app.route('/', methods=['GET', 'POST'])
def show_image():
	create_plots()
	return render_template('index.html')

if __name__ == '__main__':
	app.run()
