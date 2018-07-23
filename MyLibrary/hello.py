from __future__ import unicode_literals
from imapclient import IMAPClient
from email.mime.text import MIMEText
import imaplib
import smtplib
import random
import time
import datetime

class imap_test(object):
    '''test imap server: working with folders and messages + IDLE mod of server

    Attributes:
        host:
        username:
        password:
    '''

    def __init__(self, host, username, password):
        """create server object with credentials"""
        self.host = host
        self.username = username
        self.password = password
        self.server = self.login()

    def login(self, ssl = False):
        '''try to login over imap to server with credential in attributes
            return server object
        '''
        server = IMAPClient(self.host, use_uid=True, ssl=ssl)
        try:
            server.login(self.username, self.password)
            print('login successful')
            return server
        except imaplib.IMAP4.error as err:
            print("login failed:\nHost = ", self.host, "\nUser = ", self.username, "\nPW  = ", self.password)
            print(str(err))
            raise RuntimeError("can't login: ", err)

    def test_name_folder(self, name):
        '''return true if this folder already exists
        '''
        xlist = self.server.xlist_folders()
        for names in xlist:
            if str(names[2]) == name:
                return False
        return True

    def test_create_folder(self, test_folder = "TEST_folder"):
        '''try to create folder, if already exists it create another one and test it... return name of tested folder
        '''
        i = 0
        while not self.test_name_folder(test_folder):
            i += 1
            test_folder = test_folder + str(i)
        try:
            self.server.create_folder(test_folder)
        except imaplib.IMAP4.error as err:
            if str(err) == "create failed: CREATE Mailbox already exists":
                print("folder %s already exists..." %test_folder)
                raise RuntimeError("folder already exist: ", err)
            else:
                print("ERROR: ", err)
            #return err
            raise RuntimeError("unknow error: ", err)
        except:
            print("nejaka jina chyba:", err)
            #return err
            raise RuntimeError("unknow error: ", err)
        try:
            self.server.select_folder(test_folder)
        except imaplib.IMAP4.error as err:
            print("TEST1a - create folder - FAILED")
            print(str(err))
            return False
        else:
            print("TEST1a - create folder - OK")
            self.server.close_folder()
            return test_folder

    def test_folder_cs(self, test_folder = "TEST_folder"):
        '''Try to create swapcased folder if it's not possible => OK
        '''
        swap_folder = test_folder.swapcase()
        if self.test_name_folder(test_folder):
            i = 0
            while not self.test_name_folder(test_folder):
                i += 1
                test_folder = test_folder + str(i)
            self.server.create_folder(test_folder)
        try:
            self.server.create_folder(swap_folder)
        except imaplib.IMAP4.error as err:
            if str(err) == "create failed: CREATE Mailbox already exists":
                print("TEST1b - case sensitivity - OK")
                return True
        except:
            print("nejaka jina chyba:", err)
            raise RuntimeError("unknow error: ", err)
        else:
            print("TEST1b - case sensitivity - FAILED")
            print(str(err))
            return False

    def test_rename_folder(self, test_folder = "TEST_folder"):
        '''it rename folder to another one. returns name of new folder 
        !!!! It doesn't create old folder!!!
        '''
        xlist = self.server.xlist_folders()
        if not self.test_name_folder(test_folder):
            new_folder = test_folder + '-new'
            i = 0
            while not self.test_name_folder(new_folder):
                i += 1
                new_folder = new_folder + str(i)
            try:
                self.server.rename_folder(test_folder, new_folder)
                try:
                    self.server.select_folder(new_folder)
                except imaplib.IMAP4.error as err:
                    #print("TEST2  - rename folder - FAILED")
                    #print(str(err))
                    raise RuntimeError("can't open new folder: ", err)
                else:
                    #print("TEST2  - rename folder - OK")
                    self.server.close_folder()
                    return new_folder
            except imaplib.IMAP4.error as err:
                #print("TEST2  - rename folder - FAILED")
                #print(str(err))
                raise RuntimeError("rename folder failed: ", err)
        else:
            print("Folder to rename doesn't exists...")
            return False                                                      #DOPSAT VLASTNI EXCEPTION!!!!

    def send_test_msg(self):
        '''send MSG with random subject to self
        return this message...
        '''
        test_msg = MIMEText('Testovaci zprava...')
        test_msg['Subject'] = 'TEST email c.: ' + str(random.randrange(10000,99999))
        test_msg['From'] = self.username
        test_msg['To'] = self.username
        try:
            s = smtplib.SMTP(self.host)
            try:
                s.send_message(test_msg)
                s.quit()
                return test_msg
            except smtplib.SMTPException as err:
                print(str(err))
                raise RuntimeError("unable to send MSG:", err)
        except smtplib.SMTPException as err:
            print(str(err))
            raise RuntimeError("can't setup connection to SMTP server:", err)

    def test_idle_mode(self):
        self.send_test_msg()
        self.server.select_folder('INBOX')
        try:
            self.server.idle()
        except imaplib.IMAP4.error as err:
            print("TEST3a - IDLE MODE - FAILED")
            print(str(err))
            raise RuntimeError("Can't start IDLE mode:", err)
        try:    
            check = self.server.idle_check(5)
            self.server.idle_done()
            self.server.close_folder()
            if check == []:
                print("TEST3a - IDLE MODE - FAILED")
                return False
            else:
                print("TEST3a - IDLE MODE - OK")
                return True
        except imaplib.IMAP4.error as err:
            print("TEST3a - IDLE MODE - FAILED")
            print(str(err))
            raise RuntimeError("Can't start waiting mode:", err)

    def find_msg_by_subject(self, folder = 'INBOX', subject = None):
        '''it try to find latest message in specific folder by msg's subject
        return ID of this msg or false if nothing is found
        '''
        try:
            self.server.select_folder(folder)
        except imaplib.IMAP4.error as err:
            raise RuntimeError("This folder doesn't exists....", err)

        msg = self.server.search([b'NOT', b'DELETED'])
        msg_ID = None
        if msg != []:
            for x in reversed(msg):
                try:
                    msg_details = (self.server.fetch([x], 'ENVELOPE'))
                    subject2 = msg_details[x][b'ENVELOPE'].subject
                    if str(subject2.decode("utf-8")) == str(subject):
                        msg_ID = x
                        break
                except imaplib.IMAP4.error as err:
                    #print("TEST3b - received MSG - FAILED")
                    #print(str(err))  
                    self.server.close_folder()
                    raise RuntimeError("Can't fetch msg from server:", err)
            self.server.close_folder()
        else:
            #print("MSG not found...")
            self.server.close_folder()
            return False
        if msg_ID == None:
            #print("TEST3b - received MSG - FAILED")
            return False
        else:
            #print("TEST3b - received MSG - OK")
            return msg_ID

    def test_received_msg(self):
        '''It send MSG and than try to received it...
        return msg_ID
        '''
        test_msg = self.send_test_msg()
        #test_msg['Subject']
        time.sleep(2)
        return self.find_msg_by_subject(subject = test_msg['Subject'])

    def test_search_msg(self):
        '''try to find any today MSG...
        '''
        self.server.select_folder('INBOX')
        try:
            if self.server.search([u'SINCE', datetime.date.today()]):
                self.server.close_folder()
                print("TEST3c - SEARCHING MSG - OK")
                return True
            else:
                print("TEST3c - SEARCHING MSG - FAILED")
                return False
        except imaplib.IMAP4.error as err:
            print("TEST3c - SEARCHING MSG - FAILED")
            print(str(err))
            raise RuntimeError("Can't search in server:", err)

    def test_copy_msg(self, ID = None, folder_from = 'INBOX',folder_to = 'TEST_folder'):
        '''try copy MSG with specific ID and folder and than find this MSG in new folder...
        default folder_from is 'INBOX'
        with no ID it send MSG and this msg copy to: folder_to if this folder doesn't exist it will create another one
        return name of folder where MSG was sent
        '''
        if ID == None:
            ID = self.test_received_msg()

        try:
            self.server.select_folder(folder_to)
            self.server.close_folder()
        except imaplib.IMAP4.error as err:
            folder_to = self.test_create_folder(folder_to)

        try:
            self.server.select_folder(folder_from)
        except imaplib.IMAP4.error as err:
            raise RuntimeError("Unable to select this folder:", folder_from , err)

        msg_details = (self.server.fetch([ID],'ENVELOPE'))
        subject = (msg_details[ID].get(b'ENVELOPE')).subject

        try:
            self.server.copy(ID, folder_to)
        except imaplib.IMAP4.error as err:
            print("TEST4  - COPY MSG - FAILED")
            print(str(err))
            return False
        except:
            pass
        return self.find_msg_by_subject(folder_to, subject.decode("utf-8"))

    def test_del_MSG(self, ID = None, folder = 'INBOX'):
        '''try to delete MSG
        return True if is this MSG deleted...
        '''
        try:
            self.server.select_folder(folder)
        except imaplib.IMAP4.error as err:
            raise RuntimeError("Unable to select this folder:", folder , err)

        try:
            self.server.delete_messages(ID)
        except imaplib.IMAP4.error as err:
            #print("TEST5  - DELETE MSG - FAILED")
            #print(str(err))
            return False
        IDs = self.server.search(['NOT', 'DELETED'])
        if ID in IDs:
            #print("TEST5  - DELETE MSG - FAILED")
            return False
        else:
            #print("TEST5  - DELETE MSG - OK")
            return True
        self.server.close_folder()

    def flagged_msg(self, ID = None, folder = 'INBOX'):
        '''to specific msg in folder add flagged
        '''

'''
    #TEST6 ADD FLAG TO MSG
    try:
        server.select_folder(new_folder)
        try:
            flag = server.add_flags(copy_msg_ID,'\Flagged')
        except imaplib.IMAP4.error as err:
            print("TEST6  - FLAGED MSG - FAILED")
            print(str(err))
        #flag = server.add_flags(copy_msg_ID,'\Answered')
        try:
            if b'\\Flagged' in flag[1]:
                print("TEST6  - FLAGED MSG - OK")
            else:
                print("TEST6  - FLAGED MSG - FAILED")
        except:
            print("TEST6  - FLAGED MSG - FAILED")
        server.close_folder
    except imaplib.IMAP4.error as err:
        print("TEST6  - FLAGED MSG - FAILED")
        print(str(err))

    #TEST7 DELETE FOLDER
    try:
        server.delete_folder(new_folder)
        try:
            server.select_folder(new_folder)
        except imaplib.IMAP4.error as err:
            print("TEST7  - delete folder - OK")
        else:
            print("TEST7  - delete folder - FAILED")
            print(str(err))
    except imaplib.IMAP4.error as err:
        print("TEST7  - delete folder - FAILED")
        print(str(err))



    server.close_folder


    server.logout()
 '''

host = 'super-test.com'
username = 'alpha@super-test.com'
pw = 'a'



connection = imap_test(host, username, pw)

#print(connection.test_name_folder("NAme"))

#print(connection.test_rename_folder("TEST_FOLDER"))
#connection.test_received_msg()
print(connection.test_received_msg())

#print(test_search_msg())
'''
try:
    session = serv.login()
except RuntimeError as err:
    print(err)
'''
