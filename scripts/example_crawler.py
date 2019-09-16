import time
import Queue
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException


def crawl(url_to_open, driver_path, binary_path, log_extraction_script, page_load_timeout=60, file_write_timeout=3):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-application-cache')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--no-sandbox')    
    chrome_options.add_argument('--chrome-binary=' + binary_path)
    chrome_options.binary_location = binary_path

    driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
    driver.set_page_load_timeout(page_load_timeout)    

    try:
        driver.get(url_to_open)
        time.sleep(file_write_timeout)
        try:
            driver.execute_script(log_extraction_script)
        except BaseException as ex:
            print '[Main Frame] Something went wrong: ' + str(ex)
            pass

        time.sleep(file_write_timeout)

        # For crawling sub frames
        iframe_elements = driver.find_elements_by_tag_name('iframe')
        iframe_elements_queue = Queue.Queue()

        for iframe_element in iframe_elements:
            iframe_elements_queue.put((iframe_element, []))

        while not iframe_elements_queue.empty():
            try:
                iframe_holder = iframe_elements_queue.get()
                iframe = iframe_holder[0]
                iframe_parents = iframe_holder[1]
                
                for parent in iframe_parents:
                    driver.switch_to.frame(parent)
                
                iframe_parents.append(iframe)
                driver.switch_to.frame(iframe)

                driver.execute_script(log_extraction_script)
                time.sleep(file_write_timeout)
                
                child_iframe_elements = driver.find_elements_by_tag_name('iframe')
                for child_iframe_element in child_iframe_elements:
                    iframe_elements_queue.put((child_iframe_element, iframe_parents))

                driver.switch_to.default_content()

            except StaleElementReferenceException:
                print '[Sub Frame] Stale element encountered'
            
            except BaseException as exx:
                pass

    except BaseException as ex:
        print 'Something went wrong: ' + str(ex)
        pass

    finally:
        driver.quit()


driver_path = 'PATH_TO_CHROMEDRIVER' 
# tested with ChromeDriver version 2.42
binary_path = 'PATH_TO_BINARY'
log_extraction_script = "document.createCDATASection('NOTVERYUNIQUESTRING');"
url_to_open = 'https://www.google.com'

print 'Opening URL: ' + url_to_open
crawl(url_to_open, driver_path, binary_path, log_extraction_script)
# logs will be stored in `rendering_stream` in home directory
