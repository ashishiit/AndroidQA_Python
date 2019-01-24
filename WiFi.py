import android,time,re
import TestLibConfig,TestUtils
import traceback
import MotoSettings

WIFI_SETTING_ACTIVITY='com.android.settings/com.android.settings.wifi.WifiSettings'
WIFI_INTENT  = 'am start -n %s --activity-clear-top'%WIFI_SETTING_ACTIVITY
#SETTING_INTENT='am start -n com.android.settings/com.android.settings.Settings'
WIFI_ADVANCED= 'am start -n com.android.settings/.wifi.AdvancedSettings'
WIFI = 'Wi-Fi'

IPV4_REGEX = '((?:[0-9]{1,3}\.){3}[0-9]{1,3})'
IPV6_REGEX = '((?:[0-9A-Fa-f]{3,4}:){7}[0-9A-Fa-f]{4})'
PHONE_STATUS_INTENT = 'am start -a android.intent.action.MAIN -n com.android.settings/.deviceinfo.Status --activity-clear-top'
ADB_CMD_GET_IP_WLAN0 = (["shell", "ifconfig", "wlan0"])

# TODO: Use unicode text instead of regex for Wi-Fi.
class WiFi:
	WIFI_SETTING_ACTIVITY = WIFI_SETTING_ACTIVITY

	'''The class includes all Wi-Fi UI operations'''
	def __init__(self, android):
		self.android = android

	def launch(self):
		"""
		Description:
			Launch WiFi Settings

		Required arguments:
			NONE

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		self.launch_by_intent()

	def launch_by_intent(self):
		"""
		Description:
			Launch WiFi settings by Intent
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if self.in_wifi():
			return
		self.android.device.sh(WIFI_INTENT)
		WIFI_SETTING_WIDGETS = [self.android.ui.widgetspec(id='action_bar_title', regexp='Wi.Fi'), 
					self.android.ui.widgetspec(regexp='Wi.*Fi')]
		self.android.ui.waitfor(anyof=WIFI_SETTING_WIDGETS, timeout=5)
		time.sleep(3)

	def launch_wifi_advanced(self):
		"""
		Description:
			Launch wifi advanced settings
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		self.android.device.sh(WIFI_ADVANCED)
		self.android.ui.waitfor(text='Advanced')

	def in_wifi(self):
		"""
		Description:
			Check if current screen is WiFi settings
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			Return True if yes, False otherwise
		"""
		return self.android.ui.window() == self.WIFI_SETTING_ACTIVITY

	def enable_wifi(self):
		"""
		Description:
			Turn on Wifi
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if self.is_turnon() is False:
			self.android.ui.screen().widget(type='android.widget.Switch').tap()
			## china product will promt for WLAN data usage confirm dialog sometimes
			try:
				self.android.ui.waitfor(id='titleName', text='Confirm', timeout=3)
				self.android.ui.screen().widget(id='permit_bn').tap()
				time.sleep(3*TestLibConfig.SLEEP_MULTIPLIER)
			except:
				pass
			#Handle "Warning: Turning ON Wi-Fi will turn OFF Mobile Hotspot" dialogue
			try:
				self.android.ui.waitfor(regexp='(?i)will turn off mobile hotspot', timeout=2)
				self.android.ui.waitfor(id='button1').tap()
			except:
				pass
		# Add step to make sure wifi is on after tap
		self.android.ui.waitfor(anyof=[self.android.ui.widgetspec(id='summary'),self.android.ui.widgetspec(id='switch_widget',text='ON')])

	def enable_wifi_cmd(self):
		"""
		Description:
			Turn on Wifi using command line
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if self.is_turnon() is False:
			cmd_on = "svc wifi enable"
			self.android.device.sh(cmd_on)
			time.sleep(3*TestLibConfig.SLEEP_MULTIPLIER)
		# Add step to make sure wifi is on after tap
		self.android.ui.waitfor(anyof=[self.android.ui.widgetspec(id='summary'),self.android.ui.widgetspec(id='switch_widget',text='ON')])

	def disable_wifi(self):
		"""
		Description:
			Turn off Wifi
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if self.is_turnon():
			self.android.ui.screen().widget(type='android.widget.Switch').tap()
			time.sleep(1)
			#sometimes 'WiFi options' prompts
			try:
				self.android.ui.waitfor(text='Keep Wi-Fi off', timeout=5).tap()
			except:
				pass
			
			time.sleep(3)
			## make sure no wifi ap listed after turn off.
			ap_list = self.android.ui.screen().widget(id='container_material')
			summarys = ap_list.xpath(xpr='/*@@id=summary')
			while len(summarys) > 0:
				s = summarys.pop()
				## handle the 'When opening apps, tell me when Wi-Fi is available'
				## or 'notify me when Wi-Fi is available'
				if s.text().find('me when Wi-Fi is available') != -1:
					continue
				elif s.text().find('To see available networks') != -1:
					continue
				else:
					print s.text()
					raise Exception('Cannot disable the wifi setting.')
			if self.android.ui.screen().widget(type='android.widget.Switch').is_checked():
				raise Exception('Cannot disable the wifi setting.')

	def disable_wifi_cmd(self):
		"""
		Description:
			Turn off Wifi using command line
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if self.is_turnon():
			cmd_off = "svc wifi disable"
			self.android.device.sh(cmd_off)
			#sometimes 'WiFi options' prompts
			try:
				self.android.ui.waitfor(text='Keep Wi-Fi off', timeout=5).tap()
			except:
				pass

		self.android.ui.waitfor(regexp='turn Wi.Fi on')

	def is_turnon(self):
		"""
		Description:
			Check if WiFi is on
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			Return True if Wifi is on, False otherwise
		"""
		self.launch()
		## shamu
		w = self.android.ui.screen().widget(id='switch_text')
		if w and w.text() =='Off':
			return False
		elif w and w.text() == 'On':
			return True

		#everything else
		return self.android.ui.screen().widget(type='android.widget.Switch').is_checked()

	def scan(self):
		"""
		Description:
			Scan for available WiFi

		Required arguments:
			NONE

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		self.launch()
		self.enable_wifi()
		self.android.input.menu()
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		self.android.ui.waitfor(text='Scan').tap()
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)

	def connect_ap(self, ap_name, ap_password=None, forget_ap=True):
		"""
		Description:
			Try connect to the given ap 3 times

		Required arguments:
			* ap_name: the AP to connect to

		Optional arguments:
			* ap_password: the password for the AP
			* forget_ap: flag to indicate if you want to forget the AP previous connection history and reconnect or not.
				True to forget and reconnect, False to use remembered connection.

		Return value:
			NONE
		"""
		for i in range(3):
			self.android.home.home()
			try:
				if self.my_connect(ap_name,ap_password, forget_ap): return
			except:
				print 'connect wifi error'
		raise Exception('Cannot connect to ' + ap_name)

	def my_connect(self, ap_name, ap_password=None, forget_ap=True):
		"""
		Description:
			Connect to a specific AP
		Required arguments:
			* ap_name: the AP to connect to
		Optional arguments:
			* ap_password: the password for the AP
			* forget_ap: flag to indicate if you want to forget the AP previous connection history and reconnect or not.
				True to forget and reconnect, False to use remembered connection.
		Return value:
			Return True if AP is connected, False otherwise
		"""
		self.enable_wifi()
		if self.is_connect_ap(ap_name,2): #Only check 2 times
			return True
		# since the AP entry could be shifting up or down, the scrollto may tap the wrong AP entry
		# retry 3 time to be sure the correct AP is tapped
		for x in range(3):
			self.android.ui.scrollto(text=ap_name).tap()
			time.sleep(3)
			if self.android.ui.screen().widget(text=ap_name)!=None:
				break
			self.android.input.back()
		if forget_ap:
			# If there is any connection history for this ap, forget it
			m_forget= self.android.ui.screen().widget(text='Forget')
			if  m_forget is not None:
				m_forget.tap()
				time.sleep(10*TestLibConfig.SLEEP_MULTIPLIER)
				self.android.ui.scrollto(text=ap_name).tap()

		## check if password is required for connecto to this AP.
		try:
			anyof=[self.android.ui.widgetspec(id='com.android.settings:id/password'),self.android.ui.widgetspec(id='password'), self.android.ui.widgetspec(id='password_edit')]
			self.android.ui.scrollto(anyof=anyof).tap()
			ask_pwd = True
		except:
			## no password required.
			ask_pwd = False

		## password is given and UI allow password enter.
		if ap_password is not None and ask_pwd:#Connect to secured AP
			anyof=[self.android.ui.widgetspec(id='com.android.settings:id/password'),self.android.ui.widgetspec(id='password'), self.android.ui.widgetspec(id='password_edit')]
			self.android.ui.scrollto(anyof=anyof).tap()
			self.android.testutils.hide_soft_key()
			self.android.input.text(ap_password)
		s = self.android.ui.screen()
		if s.widget(text='Connect')!=None:
			s.widget(text='Connect').tap()
		elif s.widget(text='Cancel')!=None:
			s.widget(text='Cancel').tap()
		return self.is_connect_ap(ap_name,5)

	def is_connect_ap(self,ap_name,count):
		"""
		Description:
			Check the connection to a specific AP
		Required arguments:
			* ap_name: the name of the AP
			* count: how many times to check
		Optional arguments:
			NONE
		Return value:
			Return True if the AP is connected, False otherwise
		"""
		self.launch_by_intent()
		for x in range(count):
			time.sleep(10 * TestLibConfig.SLEEP_MULTIPLIER)
			widgets=self.android.ui.screen().widgets(anyof=[self.android.ui.widgetspec(id='summary'),self.android.ui.widgetspec(id='title')])
			for i in range(0,len(widgets)-1):
					if widgets[i].id() == 'title' and widgets[i].text() == ap_name:
						if widgets[i+1].id() == 'summary' and widgets[i+1].text() == 'Connected':
							return True
		return False

# NOTE: Commenting out this method since it's not working in some location.
#	def is_connect_ap_cmd(self,ap_name,count):
#		"""
#		Description:
#			Check the connection to a specific AP using command line
#		Required arguments:
#			* count: how many times to check
#		Optional arguments:
#			NONE
#		Return value:
#			Return True if the AP is connected, False otherwise
#		"""
#		self.launch_by_intent()
#		for x in range(count):
#			time.sleep(10 * TestLibConfig.SLEEP_MULTIPLIER)
#			cmd="busybox ifconfig | busybox tail -10 | busybox grep 'inet addr:10'"
#			ipaddress=self.android.device.sh(cmd)
#			if re.search('inet addr:10',ipaddress) is not None:
#				return True
#		return False

	def wait_connect(self, timeout):
		"""
		Description:
			Wait for the WiFi connection icon to appear on status bar

		Required arguments:
			* timeout: how many seconds to wait for

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		for i in range(timeout):
			if self.is_connected() is True:
				return
			time.sleep(1)
		raise Exception('Cannot connect to the AP in %d Seconds' %timeout)

	def wait_disconnect(self, timeout):
		"""
		Description:
			Wait for the WiFi connection icon to disappear on the status bar

		Required arguments:
			* timeout: how many seconds to wait for

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		for i in range(timeout):
			if self.is_connected() is False:
				return
			time.sleep(1)
		raise Exception('Cannot disconnect to the AP in %d Seconds' %timeout)

	def is_connected(self):
		"""
		Description:
			Check if WiFi is connected based on the icon on status bar

		Required arguments:
			NONE

		Optional arguments:
			NONE

		Return value:
			Return True if connected, False otherwise
		"""
		return self.android.motoSettings.check_data_connection('wifi')

	def watch_connection(self, timeout):
		"""
		Description:
			Print the WiFi status to Console

		Required arguments:
			* timeout: how many times to print the connection status

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		for i in range(timeout):
			t=time.strftime('%X %x %Z')
			if self.is_connected() is False:
				print 'The WiFi lost the connection with the AP at : ',t
			else:
				print 'The WiFi connect with the AP at :',t
			time.sleep(1)

	def forget_ap(self, ap_name):
		"""
		Description:
			Forget the specific AP

		Required arguments:
			* ap_name: the name of the AP

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		self.launch()
		self.enable_wifi()
		self.android.ui.scrollto(text=ap_name).tap()
		self.android.ui.waitfor(text='Forget').tap()
		#2010-6-2 Zou Jinde remark the line.
		#self.wait_disconnect(120) #After forget AP, the wifi status may not disconnect

	def add_ap(self, ap_name, password=None, security=None):
		"""
		Description:
			Add the specific AP
		Required arguments:
			* ap_name: the name of the AP
		Optional arguments:
			password: the password of the AP
			security: the security type of the AP
		Return value:
			None
		"""
		self.launch()
		self.enable_wifi()

		try:
			self.android.ui.scrollto(text=ap_name)
			self.forget_ap(ap_name)
			time.sleep(2)
		except:
			if self.android.ui.screen().widget(id='button2', text='Cancel'):
				self.android.ui.screen().widget(id='button2', text='Cancel').tap()
				time.sleep(1)
		# Tap the "add" button 3 times
		for i in range(0, 3):
			if self.android.ui.screen().widget(id='alertTitle', text='Add network'):
				break
			try:
				self.android.testutils.xpath1(xpr='*@@drawables=ic_menu_add_dark.png').tap()
				self.android.ui.waitfor(id='alertTitle', text='Add network', timeout=3)
				break
			except:
				pass

		self.android.ui.waitfor(id='ssid', timeout=5).tap()
		time.sleep(0.5)
		self.android.input.text(ap_name)
		self.android.testutils.hide_soft_key()

		if security is not None:
			# Find the security spinner.
			securityWidget = self.android.ui.scrollto(id='security')

			# Change the security type, if needed.
			if self.android.testutils.xpath(securityWidget, '@@id=text1')[0].text() != security:
				securityWidget.tap()
				time.sleep(0.5)
				try:
					self.android.ui.scrollto(id='text1', regexp=security).tap()
					time.sleep(1)
				except:
					# Cannot find the specified security type.  Raise exception
					securityOptions = [w.text() for w in self.android.ui.screen().widgets(id='text1')]
					failMsg = 'Cannot find security type "%s".  Here are the available options: "%s".' %\
							  (security, securityOptions)
					self.android.input.back()
					self.android.input.back()
					raise Exception(failMsg)

		# Configure the password if needed.
		if password is not None:
			# Find the password spinner
			passwordWidget = self.android.ui.scrollto(id='password')

			passwordWidget.tap()
			time.sleep(1)
			self.android.input.text(password)
			time.sleep(0.5)
			self.android.testutils.hide_soft_key()
			time.sleep(0.5)
		
		self.android.ui.screen().widget(id='button1').tap()
		try:
			self.android.ui.waitfor(noneof=self.android.ui.widgetspec(id='alertTitle', text='Add network'), timeout=3)
		except:
			self.android.ui.screen().widget(id='button2').tap()
			time.sleep(0.5)
			raise Exception('Cannot find the ap.')

	def set_static_ip(self,ip):
		"""
		Description:
			Set static IP in WiFi advanced settings

		Required arguments:
			* ip: the static IP address

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		self.launch_wifi_advanced()
		self.android.ui.scrollto(text='IP address')
		#Turn on static IP
		self.android.testutils.touch_check_box('Use static IP',True)
		#Input IP address
		self.android.testutils.input_dialog('IP address',ip)
		#Input Gateway
		self.android.testutils.input_dialog('Gateway','192.168.0.1')
		#Input Netmask
		self.android.testutils.input_dialog('Netmask','255.255.255.0')
		#Input DNS 1
		self.android.testutils.input_dialog('DNS 1','0.0.0.0')

	def add_station(self,SSID,password):
		"""
		Description:
			Add ad-hoc station

		Required arguments:
			* SSID: the SSID of the wireless network
			* password: the password of the wireless network

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		self.enable_wifi()
		#Find SSID
		try:
			self.android.ui.scrollto(text=SSID) #print_log("SSID already exists : " + SSID)
			return
		except:
			pass
		self.android.ui.scrollto(text='Add Wi-Fi network').tap() #To show dialog
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		#Input SSID
		self.android.input.text(SSID)
		#Select the Peer to peer check box in dialog
		self.android.ui.scrollto(id='network_mode_checkbox').tap()
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		#Select the securitype
		self.android.ui.scrollto(text='None').tap()
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		self.android.ui.scrollto(text='WEP').tap()
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		#Input password
		self.android.ui.scrollto(id='password_edit').tap() #Set focus on password box
		self.android.testutils.hide_soft_key()
		self.android.input.text(password)
		time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
		#Find the save button
		self.android.ui.scrollto(text='Save').tap()

	def ping_ip(self,ip):
		"""
		Description:
			Ping IP address

		Required arguments:
			* ip: the IP address to ping

		Optional arguments:
			NONE

		Return value:
			NONE
		"""
		cmd = 'ping -c 1 ' + ip
		for i in range(20):
			time.sleep(TestLibConfig.SLEEP_MULTIPLIER)
			out=self.android.device.sh(cmd)
			if out.find('1 packets transmitted, 1 received,')>0:
				return
			else:
				android.log.error('ping_ip_'+str(i),out)
		raise Exception('Fail to ping ip : '+ip)

	#Open the WiFi direct UI
	def open_wifi_direct(self):
		self.enable_wifi()
		a = self.android
		a.input.menu()
		time.sleep(3) # Must sleep for the menu showing is slow
		a.ui.screen().widget(text='Wi-Fi Direct').tap()
		time.sleep(3)
		if a.ui.screen().widget(text='Peer devices')==None:
			raise Exception('Cannot open the WiFi direct UI.')

	def set_wifi_status(self, onOff):
		"""
		Description:
			Set Wifi on or off
		Required arguments:
			onOff: True turn on Wifi, Flase otherwise
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		if onOff:
			self.enable_wifi()
		else:
			self.disable_wifi()

	def set_wifi_notification(self, onOff):
		"""
		Description:
			set wifi notification on or off
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		self.launch()
		if onOff:
			self.android.testutils.touch_check_box("Notify me", True)
		else:
			self.android.testutils.touch_check_box("Notify me", False)

	def set_auto_connect_wifi(self, onOff):
		"""
		Description:
			set auto connect wifi on or off
		Required arguments:
			NONE
		Optional arguments:
			NONE
		Return value:
			NONE
		"""
		self.launch()
		if onOff:
			self.android.testutils.touch_check_box("Auto-Connect Wi-Fi", True)
		else:
			self.android.testutils.touch_check_box("Auto-Connect Wi-Fi", False)

	def find_ap_exist(self, ap_name):
		"""
		Description:
			find wifi ap exists on wifi lise or not
		Required arguments:
			wifi ap SSID
		Optional arguments:
			NONE
		Return value:
			True = find the wifi ap on the wifi list
			False = cannot find the wifi ap on the wifi list
		"""
		self.launch()
		self.enable_wifi()
		try:
			self.android.ui.scrollto(text = ap_name)
			return True
		except:
			return False

	def change_band(self, band):
		"""
		Description:
			set the wifi frequency band
		Required arguments:
			wifi frequency band
		Optional arguments:
			NONE
		Return value:
		NONE
		"""
		self.launch()
		self.android.input.menu()
		self.android.ui.waitfor(text = 'Advanced').tap()
		self.android.ui.waitfor(id = 'action_bar_title', regexp = r'Advanced')

		self.android.ui.scrollto(regexp = 'Wi.?Fi frequency band').tap()
		self.android.ui.waitfor(id = 'alertTitle', regexp = 'Wi.?Fi frequency band')
		self.android.ui.screen().widget(text = band).tap()
                
	def check_ip(self, ssid=None, ipv6 = False):
		"""
		Description:
			Check the ip address after connecting to wifi ap.
		Required arguments:
			ssid    - The ssid for the wifi ap
		Optional arguments:
			ipv6 	- If ipv6 is True, it will return the ipv6 address
		Return value:
			IP address
		"""
		if ipv6:
			self.android.device.sh(PHONE_STATUS_INTENT)
			name = 'IP address'
			try:
				self.android.ui.waitfor(id='action_bar_title', text='Status')
			except:
				raise Exception('Cannot open phone\'s status settings page.')
    			# Find entry specified by name
			self.android.ui.scrollto(id='title', regexp=name)
			time.sleep(1)
			s = self.android.ui.screen()
			p = s.widget(id='title', regexp=name).parent(s)
			m = re.search(IPV6_REGEX, self.android.testutils.xpath(p, '@@id=summary')[0].text())
			if m:
				return m.group(1)
		else:
			return self.android.device.adb(ADB_CMD_GET_IP_WLAN0).split()[2]

	def wpsConnect(self):
		"""
		Description:
			Initiate the WPS connect on the client device.
		Required arguments:
			None
		Optional arguments:
			None
		Return vale:
			None
		"""
		self.launch()
		self.android.testutils.xpath1(xpr='*@@drawables=ic_wps_dark.png').tap()
		self.android.ui.waitfor(id='wps_dialog_txt', timeout=5)

	def wpsSuccess(self, ssid):
		"""
		Description:
			Check if the device is connected to the ssid using WPS connection.
		Required arguments:
			ssid	- the ssid for the wifi ap
		Optional arguments:
			None
		Return value:
			True	- the device is connected to the ssid
			False	- the device is not connected to the ssid
		"""
		self.android.ui.waitfor(id='wps_dialog_btn', text='OK', timeout=130)

		wps_dialog = self.android.ui.screen().widget(id='wps_dialog_txt').text()
		self.android.ui.screen().widget(id='wps_dialog_btn', text='OK').tap()

		if re.compile('Connected to Wi.Fi network "%s"'%ssid).search(wps_dialog):
			return True
		elif re.compile('WPS failed').search(wps_dialog):
			return False
		else:
			raise Exception('Unknown error.')

	def disconnectPreConnectedAps(self):
		"""
		Description:
			Disconnect all previous connected wifi aps.
		Required arguments:
			None
		Optional arguments:
			None
		Return value:
			None
		"""
		self.enable_wifi()
		time.sleep(3)
		anyof = (
			self.android.ui.widgetspec(text='Not in range'),
			self.android.ui.widgetspec(text='Connected'),
			self.android.ui.widgetspec(text='Saved'),
			self.android.ui.widgetspec(text='Disabled'),
			self.android.ui.widgetspec(text='Authentication problem')
		)
		try:
			while self.android.ui.scrollto(anyof=anyof) != None:
				self.android.ui.screen().widget(anyof=anyof).tap()
				time.sleep(1)
				self.android.ui.screen().widget(regexp="Forget").tap()
				time.sleep(1)
		except Exception as e:
			if e.message == 'WidgetNotFound: scrollto: widget not found':
				pass
		
def __test_callback(android):
	try:
		android.wifi = TestLibConfig.ProductClass(android, 'WIFI_CLASS')
	except (KeyError, TestLibConfig.ProductNotFound):
		android.wifi = WiFi(android)

android.register_module_callback(__test_callback)
