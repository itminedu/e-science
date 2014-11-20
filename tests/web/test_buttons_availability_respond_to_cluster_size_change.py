# -*- coding: utf-8 -*-
'''
This script is a test generator and checks that the buttons are enabled or disabled upon cluster_size change

@author: Ioannis Stenos, Nick Vrionis
'''
from selenium import webdriver
import sys
from os.path import join, dirname, abspath
sys.path.append(join(dirname(abspath(__file__)), '../..'))
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from ConfigParser import RawConfigParser, NoSectionError
from okeanos_utils import check_quota, get_flavor_id
import unittest, time, re

BASE_DIR = join(dirname(abspath(__file__)), "../..")

class test_buttons_availability_respond_to_cluster_size_change(unittest.TestCase):
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
        except NoSectionError:
            self.token = 'INVALID_TOKEN'
            self.auth_url = "INVALID_AUTH_URL"
            self.base_url = "INVALID_APP_URL"
            print 'Current authentication details are kept off source control. ' \
                  '\nUpdate your .config.txt file in <projectroot>/.private/'
    
    def test_buttons_availability_respond_to_cluster_size_change(self):
        driver = self.driver
        driver.get(self.base_url + "#/homepage")
        driver.find_element_by_id("id_login").click()     
        for i in range(30):
            try:
                if "~Okeanos Token" == driver.find_element_by_css_selector("h2").text: break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        driver.find_element_by_id("token").clear()
        driver.find_element_by_id("token").send_keys(self.token)               
        driver.find_element_by_xpath("//button[@type='login']").click()
        if (self.is_element_present(By.XPATH, "//div[@id='id_alert_wrongtoken']/strong") == True):
            self.assertTrue(False,'Invalid token')
        for i in range(30):
            try:
                if "Welcome" == driver.find_element_by_css_selector("h3").text: break
            except: pass
            time.sleep(1)
        else: self.fail("time out")       
        driver.find_element_by_id("id_services_dd").click()
        driver.find_element_by_id("id_create_cluster").click()
        for i in range(60):
            try:
                if "Hadoop Cluster Configuration" == driver.find_element_by_css_selector("h3").text: break
            except: pass
            time.sleep(1)
        current_cluster_size = 2
        cluster_sizes = driver.find_element_by_id("size_of_cluster").text
        try:
            current_cluster_size = int(cluster_sizes.rsplit('\n', 1)[-1])
        except:
            self.assertTrue(False,'Not enought vms to run the test')
        Select(driver.find_element_by_id("size_of_cluster")).select_by_visible_text(cluster_sizes.rsplit('\n', 1)[-1])
        user_quota = check_quota(self.token)
        kamaki_flavors = get_flavor_id(self.token)
        for flavor in ['cpus' , 'ram' , 'disk']:
            for item in kamaki_flavors[flavor]:
                button_id = 'master' + '_' + flavor + '_' + str(item)
                if ((user_quota[flavor]['available']-(item + (current_cluster_size-1)*kamaki_flavors[flavor][0])) >= 0):
                    on = driver.find_element_by_id(button_id)
                    try: self.assertTrue(on.is_enabled())
                    except AssertionError as e: self.verificationErrors.append(str(e))
                else:
                    off = driver.find_element_by_id(button_id)
                    try: self.assertFalse(off.is_enabled())
                    except AssertionError as e: self.verificationErrors.append(str(e))
        for flavor in ['cpus' , 'ram' , 'disk']:
            for item in kamaki_flavors[flavor]:
                button_id = 'slaves' + '_' + flavor + '_' + str(item)
                if ((user_quota[flavor]['available']-(kamaki_flavors[flavor][0] + (current_cluster_size-1)*item)) >= 0):
                    on = driver.find_element_by_id(button_id)
                    try: self.assertTrue(on.is_enabled())
                    except AssertionError as e: self.verificationErrors.append(str(e))
                else:
                    off = driver.find_element_by_id(button_id)
                    try: self.assertFalse(off.is_enabled())
                    except AssertionError as e: self.verificationErrors.append(str(e))

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

if __name__ == "__main__":
    unittest.main()
