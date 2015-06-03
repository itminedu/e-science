#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import logging
from os.path import join, dirname, abspath
import subprocess
from ConfigParser import RawConfigParser, NoSectionError
from orka.orka.utils import get_user_clusters, ssh_call_hadoop, ssh_check_output_hadoop
import unittest
sys.path.append(dirname(abspath(__file__)))
from constants_of_tests import *
from orka.orka.cluster_errors_constants import error_fatal, const_hadoop_status_started, FNULL

BASE_DIR = join(dirname(abspath(__file__)), "../")


class EcosystemTest(unittest.TestCase):
    """
    A Test suite for testing Ecosystem components
    """
    def setUp(self):
        """
        Set up the arguments that every test will use.
        """
        parser = RawConfigParser()
        config_file = join(BASE_DIR, '.private/.config.txt')
        self.name = 'ecosystemtest'
        parser.read(config_file)
        try:
            self.token = parser.get('cloud \"~okeanos\"', 'token')
            self.auth_url = parser.get('cloud \"~okeanos\"', 'url')
            self.base_url = parser.get('deploy', 'url')
            self.project_name = parser.get('project', 'name')
            self.master_IP = parser.get('cluster', 'master_ip')
            clusters = get_user_clusters(self.token)
            self.active_cluster = None
            for cluster in clusters:
                if cluster['master_IP'] == self.master_IP:
                    if cluster['hadoop_status'] == const_hadoop_status_started:
                        self.active_cluster = cluster
                        self.wordcount_command = WORDCOUNT
                        self.hadoop_path = HADOOP_PATH
                        self.user = 'root'
                        self.VALID_DEST_DIR = '/user/hdfs'
                        self.hdfs_path = HDFS_PATH
                        break
            else:
                logging.error(' You can take file actions on active clusters with started hadoop only.')
                exit(error_fatal)
            self.opts = {'source': '', 'destination': '', 'token': self.token, 'cluster_id': self.active_cluster['id'],
                         'auth_url': self.auth_url, 'user': '', 'password': ''}
        except NoSectionError:
            self.token = 'INVALID_TOKEN'
            self.auth_url = "INVALID_AUTH_URL"
            self.base_url = "INVALID_APP_URL"
            self.project_name = "INVALID_PROJECT_NAME"
            print 'Current authentication details are kept off source control. ' \
                  '\nUpdate your .config.txt file in <projectroot>/.private/'
                  
                  
    def test_pig(self):
        """
        Test pig for hadoop ecosystem
        """
        pig_command = "export JAVA_HOME=/usr/lib/jvm/java-8-oracle; export HADOOP_HOME=/usr/local/hadoop; /usr/local/pig/bin/pig -e \"fs -mkdir /tmp/pig_test_folder\""
        ssh_call_hadoop('hduser', self.master_IP, pig_command, hadoop_path='')
        exist_check_status = ssh_call_hadoop('hduser', self.master_IP,
                                             ' dfs -test -e /tmp/{0}'.format('pig_test_folder'))
        self.assertEqual(exist_check_status, 0)
        self.addCleanup(self.delete_hdfs_files, '/tmp/pig_test_folder', prefix="-r")
    
    def put_file_to_hdfs(self, file_to_create):
        """
        Helper method to create file in Hdfs before test.
        """
        self.hadoop_local_fs_action('echo "test file for hdfs" > {0}'.format(file_to_create))
        ssh_call_hadoop(self.user, self.master_IP, ' dfs -put {0}'.format(file_to_create),
                        hadoop_path=self.hdfs_path)    
    
    def delete_hdfs_files(self, file_to_delete, prefix=""):
        """
        Helper method to delete files transfered to hdfs filesystem after test.
        """
        ssh_call_hadoop(self.user, self.master_IP, ' dfs -rm {0} {1}'.format(prefix, file_to_delete),
                        hadoop_path=self.hdfs_path)
        
    def delete_local_files(self, file_to_delete):
        """
        Helper method to delete files transfered to local filesystem after test.
        """
        if os.path.isfile(file_to_delete):
            os.remove(file_to_delete)
        else:
            print("Error: {0} test file not found".format(file_to_delete))


    def hadoop_local_fs_action(self, action):
        """
        Helper method to perform action given on local filesystem of a master VM.
        """
        subprocess.call("ssh {0}@".format(self.user) + self.master_IP + " \"" + action +
                        "\"", stderr=FNULL, shell=True)

    def tearDown(self):
        """
        tearDown method for unit test class.
        """
        print 'Cleaning up temp files'


if __name__ == '__main__':
    unittest.main()
