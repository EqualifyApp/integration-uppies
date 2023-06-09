import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
from time import time
from utils.watch import logger
from utils.auth import rabbit
from utils.metrics import (
    JUMP_COUNTER, JUMP_LATENCY,
    SUCCESS_COUNT, FAILURE_COUNT)


def jump(url, url_id):
    logger.debug(f'🌟 Starting to process: {url}')

    # Set the proxy settings using environment variables
    use_proxy = os.environ.get('USE_PROXY', 'false').lower() == 'true'
    logger.debug(f'USE_PROXY: {use_proxy} ')
    proxy_http = os.environ.get('PROXY_HTTP')
    if proxy_http:
        proxy_http = f'http://{proxy_http}'
    logger.debug(f'PROXY_HTTP: {proxy_http}')
    proxy_https = os.environ.get('PROXY_HTTPS')
    if proxy_https:
        proxy_https = f'http://{proxy_https}'
    logger.debug(f'PROXY_HTTPS: {proxy_https} ')
    proxies = {'http': proxy_http, 'https': proxy_https} if use_proxy else None
    logger.debug(f'Proxies: {proxies} ')

    # response = requests.get(url, proxies=proxies, verify=False, timeout=10)
    try:
        response = requests.head(url, proxies=proxies, verify=False, timeout=10)
        # response = session.head(url, timeout=15)
        # response = session.get(url, stream=True, timeout=15)
        headers = response.headers
        # logger.debug(f'Headers: {headers}')

        logger.debug(f'URL: {url} - Status code: {response.status_code}')

        data = {
            'status_code': response.status_code,
            'content_type': response.headers.get('Content-Type', ''),
            'response_time': response.elapsed.total_seconds(),
            'charset': response.encoding,
            'page_last_modified': response.headers.get('Last-Modified', ''),
            'content_length': response.headers.get('Content-Length', ''),
            'server': response.headers.get('Server', ''),
            'x_powered_by': response.headers.get('X-Powered-By', ''),
            'x_content_type_options':
                response.headers.get('X-Content-Type-Options', ''),

            'x_frame_options': response.headers.get('X-Frame-Options', ''),
            'x_xss_protection': response.headers.get('X-XSS-Protection', ''),
            'content_security_policy':
            response.headers.get('Content-Security-Policy', ''),

            'strict_transport_security':
            response.headers.get('Strict-Transport-Security', ''),

            'etag': response.headers.get('ETag', '')
        }
        # Replaced record_uppies with good_jump
        good_jump(url_id, data)
        SUCCESS_COUNT.labels(endpoint='/jump').inc()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {url} - {str(e)}")
        logger.debug(f"URL: {url} - Error details: {str(e)}")
        # Replaced record_uppies with bad_jump
        bad_jump(url_id, {
            'status_code': 999,
            'content_type': '',
            'response_time': 0,
            'charset': '',
            'page_last_modified': '',
            'content_length': '',
            'server': '',
            'x_powered_by': '',
            'x_content_type_options': '',
            'x_frame_options': '',
            'x_xss_protection': '',
            'content_security_policy': '',
            'strict_transport_security': '',
            'etag': ''
        })
    except UnicodeError as e:
        logger.error(f"Encoding error with URL: {url} - {str(e)}")
        logger.debug(f"URL: {url} - Error details: {str(e)}")
        # Replaced record_uppies with bad_jump
        bad_jump(url_id, {
            'status_code': 998,
            'content_type': '',
            'response_time': 0,
            'charset': '',
            'page_last_modified': '',
            'content_length': '',
            'server': '',
            'x_powered_by': '',
            'x_content_type_options': '',
            'x_frame_options': '',
            'x_xss_protection': '',
            'content_security_policy': '',
            'strict_transport_security': '',
            'etag': ''
        })
        FAILURE_COUNT.labels(endpoint='/jump').inc()

    # JUMP_COUNTER.inc()
    # JUMP_LATENCY.observe(time() - start_time)


def good_jump(url_id, data):
    message = json.dumps({"url_id": url_id, "data": data})
    logger.debug(
        f'Sending good_jump message for URL ID: {url_id} - Data: {data}')
# Send the data to the RabbitMQ queue
    queue_name = 'landing_uppies'
    channel, connection = rabbit(queue_name, message)
    if channel and connection:
        logger.info(f'🏆 Message sent to {queue_name}!')
    else:
        logger.error(f'Sick Rabbit! Sick Rabbit! Sick Rabbit! {queue_name}')

    # Send a confirmation message to the axe_speed queue
    queue_name = 'speed_uppies'
    body = 'VICTORY'
    channel, connection = rabbit(queue_name, body)
    if channel and connection:
        logger.info(f'🏆 Message sent to {queue_name}!')

        # Import and call the consume_urls function here
        from main import consume_urls
        consume_urls()

    else:
        logger.error(f'Sick Rabbit! Sick Rabbit! Sick Rabbit! {queue_name}')


def bad_jump(url_id, data):
    message = json.dumps({"url_id": url_id, "data": data})
    logger.debug(
        f'Sending good_jump message for URL ID: {url_id} - Data: {data}')
# Send the data to the RabbitMQ queue
    queue_name = 'error_uppies'
    channel, connection = rabbit(queue_name, message)
    if channel and connection:
        logger.info(f'❌ Message sent to {queue_name}!')
    else:
        logger.error(f'Sick Rabbit! Sick Rabbit! Sick Rabbit! {queue_name}')
