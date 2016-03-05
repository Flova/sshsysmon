import drivers
import inspectors
import channels
from util.log import *

def evalCriteria(statement, data):
	for k,v in data.iteritems():
		exec("%s = %s" % (k,v))
	return eval(statement)

class Monitor:
	def __init__(self, name, config):
		self._name = name
		self._driver = drivers.createDriver(config.get("driver"), config.get("config", {}))
		self._alerts = config.get("alerts", {})
		self._summary = config.get("summary", {})

		self._channels = []
		for channel_type in config["channels"]:
			channel = config["channels"][channel_type]
			inst = channels.createChannel(channel_type, channel)
			self._channels.append(inst)


	def get_alerts(self):
		for alert_type in self._alerts:
			printInfo("Checking alert: %s..." % alert_type)
			alert = self._alerts[alert_type]

			try:
				inspector = inspectors.createInspector(alert_type, self._driver)
				if not inspector:
					raise Exception("Unknown inspector type: %s" % alert_type)

				metrics = inspector.getMetrics()

				if metrics:
					for alert_name in alert:
						statement = alert[alert_name]

						try:
							if evalCriteria(statement, metrics):
								yield (True, alert_type, alert_name)
							else:
								yield (False, alert_type, alert_name)
						except Exception,e:
							yield (True, alert_type, "EVAL:" + alert_name)
							printError("Error evaluating alert: %s" % e)
				else:
					yield (True, "NO_DATA", "No data")

			except Exception,e:
				printError("Error executing inspector %s: %s" % (alert_type, e))
				yield (True, "INSPECTOR_ERROR", str(e))

	def get_fired_alerts(self):
		for fired, alert, name in self.get_alerts():
			if fired:
				yield (alert, name)

	def send_alerts(self):
		for alert_type, alert_name in self.get_fired_alerts():
			data = {
				"server" : self._name,
				"metric" : alert_type,
				"alert" : alert_name,
			}

			for channel in self._channels:
				channel.notify(data)
				yield (alert_type, alert_name)

	def printSummary(self):
		for summary_type, summary_items in self._summary.iteritems():
			try:
				inspector = inspectors.createInspector(summary_type, self._driver)
				print "## %s" % inspector.getName()
				metrics = inspector.getMetrics()

				if metrics:
					for key in summary_items:
						print "%s: %s" % (key.upper(), metrics.get(key, "<Missing>"))
				else:
					print "Unable to retrieve metrics"

			except Exception, e:
				printError("Error executing inspector %s: %s" % (summary_type, e))
			print ""


