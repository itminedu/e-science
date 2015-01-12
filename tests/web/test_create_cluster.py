# -*- coding: utf-8 -*-
'''
This script is a test for cluster creation via GUI end to end

@author: Ioannis Stenos, Nick Vrionis
'''
from selenium import webdriver
import sys, os
from os.path import join, dirname, abspath
sys.path.append(join(dirname(abspath(__file__)), '../../orka-0.1.0/orka'))
sys.path.append(join(dirname(__file__), '../../ember_django/backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from ConfigParser import RawConfigParser, NoSectionError
from okeanos_utils import check_quota, get_flavor_id, check_credentials
import unittest, time, re

BASE_DIR = join(dirname(abspath(__file__)), "../..")

class test_text_respond_to_buttons(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.verificationErrors = []
        self.accept_next_alert = True
        parser = RawConfigParser()
        config_file = join(BASE_DIR, '.private/.config.txt')
        self.name = 'testcluster'
        parser.read(config_file)
        try:
            self.token = parser.get('cloud \"~okeanos\"', 'token')
            self.auth_url = parser.get('cloud \"~okeanos\"', 'url')
            self.base_url = parser.get('deploy', 'url')
            self.project_name = parser.get('project', 'name')
            auth = check_credentials(self.token)
            try:
                list_of_projects = auth.get_projects(state='active')
            except Exception:
                self.assertTrue(False,'Could not get list of projects')
            for project in list_of_projects:
                if project['name'] == self.project_name:
                    self.project_id = project['id']
        except NoSectionError:
            self.token = 'INVALID_TOKEN'
            self.auth_url = "INVALID_AUTH_URL"
            self.base_url = "INVALID_APP_URL"
            self.project_name = "INVALID_PROJECT_NAME"
            print 'Current authentication details are kept off source control. ' \
                  '\nUpdate your .config.txt file in <projectroot>/.private/'
    
    def test_text_respond_to_buttons(self):
        driver = self.driver
        driver.get(self.base_url + "#/homepage")
        driver.find_element_by_id("id_login").click()     
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "id_title_user_login_route"))
            ) 
        except: self.fail("time out")
        driver.find_element_by_id("token").clear()
        driver.find_element_by_id("token").send_keys(self.token)               
        driver.find_element_by_xpath("//button[@type='login']").click()
        if (self.is_element_present(By.XPATH, "//div[@id='id_alert_wrongtoken']/strong") == True):
            self.assertTrue(False,'Invalid token')
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "id_title_user_welcome_route"))
            ) 
        except: self.fail("time out")     
        driver.find_element_by_id("id_services_dd").click()
        driver.find_element_by_id("id_create_cluster").click()        
        try:
            element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "id_title_cluster_create_route"))
            ) 
        except: self.fail("time out")
        auth = check_credentials(self.token)
        try:
            list_of_projects = auth.get_projects(state='active')
        except Exception:
            self.assertTrue(False,'Could not get list of projects')
        kamaki_flavors = get_flavor_id(self.token)
        user_quota = check_quota(self.token, self.project_id)
        project_details = self.project_name + '        ' + 'VMs:' + str(user_quota['cluster_size']['available']) + '  ' + 'CPUs:' + str(user_quota['cpus']['available']) + '  ' + 'RAM:' + str(user_quota['ram']['available']) + 'MB' + '  ' + 'Disk:' + str(user_quota['disk']['available']) + 'GB'                            
        Select(driver.find_element_by_id("project_id")).select_by_visible_text(project_details)                           
        driver.find_element_by_id("cluster_name").clear()
        driver.find_element_by_id("cluster_name").send_keys("mycluster")
        Select(driver.find_element_by_id("size_of_cluster")).select_by_visible_text('2')
        for role in ['master' , 'slaves']:
            for flavor in ['cpus' , 'ram' , 'disk']:
                button_id = role + '_' + flavor + '_' + str(kamaki_flavors[flavor][0])
                driver.find_element_by_id(button_id).click()
        driver.find_element_by_id("next").click()
        print 'Creating cluster...'
        for i in range(1800): 
            # wait for cluster create to finish
            try:
                if "" != driver.find_element_by_id('id_output_message').text: break
            except: pass
            time.sleep(1)
        message =  driver.find_element_by_id('id_output_message').text
        if message.rsplit(':', 1)[-1] == '8088/cluster':         
            cluster_url = message.rsplit(' ', 1)[-1]
            driver.get(cluster_url)
            print message
            #check that cluster url is up and page is running
            try: self.assertEqual("All Applications", driver.find_element_by_css_selector("h1").text)
            except AssertionError as e: self.verificationErrors.append(str(e))
        else:
            self.assertTrue(False, message)


    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
