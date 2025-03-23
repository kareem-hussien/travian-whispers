def new_func():
    """
Session Isolation Testing Tool for Travian Whispers.
This tool tests the session isolation functionality by:
1. Creating multiple isolated browser sessions
2. Testing IP assignment
3. Simulating rotation scenarios
"""
    import sys
    import os
    # Add the project root to the Python path
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Rest of your imports
    import time
    import logging
    import argparse
    import threading
    from queue import Queue
    from datetime import datetime
    from startup.session_isolation import BrowserIsolationManager
    # Clean up sessions
    browser_manager = BrowserIsolationManager()
    for user_id in TEST_USERS:
            browser_manager.cleanup_user_resources(user_id)
    
    logger.info("Concurrent sessions test completed")

    def simulate_detection_handling():
        """Simulate detection handling scenarios."""
        logger.info("Simulating detection handling...")
    
        browser_manager = BrowserIsolationManager()
    
    # Clean up existing resources
        for user_id in TEST_USERS:
            browser_manager.cleanup_user_resources(user_id)
    
        user_id = TEST_USERS[0]
    
    # Get initial configuration
        initial_config = browser_manager.get_isolated_browser_config(user_id)
        initial_ip = initial_config['ip_data']['ip'] if initial_config.get('ip_data') else None
        initial_session = initial_config['session_path']
    
        logger.info(f"Initial configuration for user {user_id}:")
        logger.info(f"  IP: {initial_ip}")
        logger.info(f"  Session: {initial_session}")
    
    # Simulate low risk detection
        result_low = browser_manager.handle_detection_risk(user_id, "low", {"source": "test"})
    
        logger.info(f"Low risk detection handling result: {result_low}")
    
    # Get updated configuration
        low_risk_config = browser_manager.get_isolated_browser_config(user_id)
        low_risk_ip = low_risk_config['ip_data']['ip'] if low_risk_config.get('ip_data') else None
        low_risk_session = low_risk_config['session_path']
    
        logger.info(f"After low risk detection for user {user_id}:")
        logger.info(f"  IP: {low_risk_ip}")
        logger.info(f"  Session: {low_risk_session}")
    
    # Verify nothing changed
        if low_risk_ip == initial_ip and low_risk_session == initial_session:
            logger.info("SUCCESS: No changes after low risk detection")
        else:
            logger.error("FAILURE: Changes detected after low risk detection")
    
    # Simulate medium risk detection
        result_medium = browser_manager.handle_detection_risk(user_id, "medium", {"source": "test"})
    
        logger.info(f"Medium risk detection handling result: {result_medium}")
    
    # Get updated configuration
        medium_risk_config = browser_manager.get_isolated_browser_config(user_id)
        medium_risk_ip = medium_risk_config['ip_data']['ip'] if medium_risk_config.get('ip_data') else None
        medium_risk_session = medium_risk_config['session_path']
    
        logger.info(f"After medium risk detection for user {user_id}:")
        logger.info(f"  IP: {medium_risk_ip}")
        logger.info(f"  Session: {medium_risk_session}")
    
    # Verify session changed but IP remained the same
        if medium_risk_ip == low_risk_ip:
            logger.info("SUCCESS: IP remained the same after medium risk detection")
        else:
            logger.error("FAILURE: IP changed after medium risk detection")
    
        if medium_risk_session != low_risk_session:
            logger.info("SUCCESS: Session was rotated after medium risk detection")
        else:
            logger.error("FAILURE: Session was not rotated after medium risk detection")
    
    # Simulate high risk detection
        result_high = browser_manager.handle_detection_risk(user_id, "high", {"source": "test"})
    
        logger.info(f"High risk detection handling result: {result_high}")
    
    # Get updated configuration
        high_risk_config = browser_manager.get_isolated_browser_config(user_id)
        high_risk_ip = high_risk_config['ip_data']['ip'] if high_risk_config.get('ip_data') else None
        high_risk_session = high_risk_config['session_path']
    
        logger.info(f"After high risk detection for user {user_id}:")
        logger.info(f"  IP: {high_risk_ip}")
        logger.info(f"  Session: {high_risk_session}")
    
    # Verify both IP and session changed
        if high_risk_ip != medium_risk_ip:
            logger.info("SUCCESS: IP was rotated after high risk detection")
        else:
            logger.error("FAILURE: IP was not rotated after high risk detection")
    
        if high_risk_session != medium_risk_session:
            logger.info("SUCCESS: Session was rotated after high risk detection")
        else:
            logger.error("FAILURE: Session was not rotated after high risk detection")
    
    # Clean up
        browser_manager.cleanup_user_resources(user_id)
    
        logger.info("Detection handling simulation completed")

        def run_all_tests():
            """Run all isolation tests."""
            logger.info("Starting isolation tests...")
        
            test_ip_assignment()
            time.sleep(1)
        
            test_browser_isolation()
            time.sleep(1)
        
            test_rotation()
            time.sleep(1)
        
            test_concurrent_sessions()
            time.sleep(1)
        
            simulate_detection_handling()
        
            logger.info("All isolation tests completed")

        if __name__ == "__main__":
            parser = argparse.ArgumentParser(description="Test session isolation functionality")
            parser.add_argument("-t", "--test", choices=["all", "ip", "browser", "rotation", "concurrent", "detection"],
                        default="all", help="Specific test to run")
        
            args = parser.parse_args()
        
            if args.test == "all":
                run_all_tests()
            elif args.test == "ip":
                test_ip_assignment()
            elif args.test == "browser":
                test_browser_isolation()
            elif args.test == "rotation":
                test_rotation()
            elif args.test == "concurrent":
                test_concurrent_sessions()
            elif args.test == "detection":
                simulate_detection_handling()

        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from startup.browser_profile import setup_browser, login
        from startup.session_isolation import BrowserIsolationManager
        from startup.ip_manager import IPManager

    # Configure logger
        logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('isolation_test.log')
        ]
    )
        logger = logging.getLogger(__name__)

# Test user IDs
    TEST_USERS = ["test_user_1", "test_user_2", "test_user_3"]

    def test_ip_assignment():
        """Test IP assignment functionality."""
        logger.info("Testing IP assignment...")
    
        ip_manager = IPManager()
    
    # Clear existing assignments
        for user_id in TEST_USERS:
            ip_manager.release_ip_for_user(user_id)
    
    # Assign IPs to each test user
        assigned_ips = {}
        for user_id in TEST_USERS:
            ip_data = ip_manager.get_ip_for_user(user_id)
            if ip_data:
                assigned_ips[user_id] = ip_data["ip"]
                logger.info(f"Assigned IP {ip_data['ip']} to user {user_id}")
            else:
                logger.error(f"Failed to assign IP to user {user_id}")
    
    # Verify unique assignments
        unique_ips = set(assigned_ips.values())
        if len(unique_ips) == len(assigned_ips):
            logger.info("SUCCESS: All users have unique IPs")
        else:
            logger.error("FAILURE: Not all users have unique IPs")
    
    # Test IP retrieval (should return the same IP)
        for user_id in TEST_USERS:
            if user_id not in assigned_ips:
                continue
            
            ip_data = ip_manager.get_ip_for_user(user_id)
            if ip_data and ip_data["ip"] == assigned_ips[user_id]:
                logger.info(f"SUCCESS: Retrieved same IP {ip_data['ip']} for user {user_id}")
            else:
                logger.error(f"FAILURE: Retrieved different IP for user {user_id}")
    
    # Release IPs
        for user_id in TEST_USERS:
            if ip_manager.release_ip_for_user(user_id):
                logger.info(f"Released IP for user {user_id}")
            else:
                logger.warning(f"No IP to release for user {user_id}")
    
        logger.info("IP assignment test completed")

    def test_browser_isolation():
        """Test browser isolation functionality."""
        logger.info("Testing browser isolation...")
    
        browser_manager = BrowserIsolationManager()
    
    # Clear existing sessions
        for user_id in TEST_USERS:
            browser_manager.session_manager.clear_user_session(user_id)
    
    # Get browser configurations for each test user
        configs = {}
        for user_id in TEST_USERS:
            config = browser_manager.get_isolated_browser_config(user_id)
            configs[user_id] = config
            logger.info(f"Created browser config for user {user_id}")
            logger.info(f"  Session path: {config['session_path']}")
            logger.info(f"  Proxy: {config['proxy']}")
            logger.info(f"  User agent: {config['user_agent'][:30]}...")
    
    # Verify unique session paths
        unique_paths = set(config['session_path'] for config in configs.values())
        if len(unique_paths) == len(configs):
            logger.info("SUCCESS: All users have unique session paths")
        else:
            logger.error("FAILURE: Not all users have unique session paths")
    
    # Verify unique proxies
        unique_proxies = set(config['proxy'] for config in configs.values() if config['proxy'])
        if len(unique_proxies) == len([c for c in configs.values() if c['proxy']]):
            logger.info("SUCCESS: All users have unique proxies")
        else:
            logger.error("FAILURE: Not all users have unique proxies")
    
    # Clean up sessions
        for user_id in TEST_USERS:
            if browser_manager.session_manager.clear_user_session(user_id):
                logger.info(f"Cleared session for user {user_id}")
            else:
                logger.warning(f"No session to clear for user {user_id}")
    
        logger.info("Browser isolation test completed")

    def test_rotation():
        """Test IP and session rotation functionality."""
        logger.info("Testing rotation functionality...")
    
        browser_manager = BrowserIsolationManager()
    
    # Clear existing sessions and IPs
        for user_id in TEST_USERS:
            browser_manager.cleanup_user_resources(user_id)
    
    # Test IP rotation
        user_id = TEST_USERS[0]
    
    # Get initial configuration
        initial_config = browser_manager.get_isolated_browser_config(user_id)
        initial_ip = initial_config['ip_data']['ip'] if initial_config.get('ip_data') else None
        initial_session = initial_config['session_path']
    
        logger.info(f"Initial configuration for user {user_id}:")
        logger.info(f"  IP: {initial_ip}")
        logger.info(f"  Session: {initial_session}")
    
    # Rotate IP only
        browser_manager.ip_manager.rotate_ip_for_user(user_id)
    
    # Get updated configuration
        ip_rotated_config = browser_manager.get_isolated_browser_config(user_id)
        ip_rotated_ip = ip_rotated_config['ip_data']['ip'] if ip_rotated_config.get('ip_data') else None
        ip_rotated_session = ip_rotated_config['session_path']
    
        logger.info(f"After IP rotation for user {user_id}:")
        logger.info(f"  IP: {ip_rotated_ip}")
        logger.info(f"  Session: {ip_rotated_session}")
    
    # Verify IP changed but session remained the same
        if ip_rotated_ip != initial_ip:
            logger.info("SUCCESS: IP was rotated")
        else:
            logger.error("FAILURE: IP was not rotated")
    
        if ip_rotated_session == initial_session:
            logger.info("SUCCESS: Session path remained the same after IP rotation")
        else:
            logger.error("FAILURE: Session path changed after IP rotation")
    
    # Rotate session only
        browser_manager.session_manager.rotate_user_session(user_id)
    
    # Get updated configuration
        session_rotated_config = browser_manager.get_isolated_browser_config(user_id)
        session_rotated_ip = session_rotated_config['ip_data']['ip'] if session_rotated_config.get('ip_data') else None
        session_rotated_session = session_rotated_config['session_path']
    
        logger.info(f"After session rotation for user {user_id}:")
        logger.info(f"  IP: {session_rotated_ip}")
        logger.info(f"  Session: {session_rotated_session}")
    
    # Verify session changed but IP remained the same
        if session_rotated_session != ip_rotated_session:
            logger.info("SUCCESS: Session was rotated")
        else:
            logger.error("FAILURE: Session was not rotated")
    
        if session_rotated_ip == ip_rotated_ip:
            logger.info("SUCCESS: IP remained the same after session rotation")
        else:
            logger.error("FAILURE: IP changed after session rotation")
    
    # Rotate entire identity
        new_config = browser_manager.rotate_user_identity(user_id)
    
    # Get updated configuration
        identity_rotated_config = browser_manager.get_isolated_browser_config(user_id)
        identity_rotated_ip = identity_rotated_config['ip_data']['ip'] if identity_rotated_config.get('ip_data') else None
        identity_rotated_session = identity_rotated_config['session_path']
    
        logger.info(f"After identity rotation for user {user_id}:")
        logger.info(f"  IP: {identity_rotated_ip}")
        logger.info(f"  Session: {identity_rotated_session}")
    
    # Verify both IP and session changed
        if identity_rotated_ip != session_rotated_ip:
            logger.info("SUCCESS: IP was rotated during identity rotation")
        else:
            logger.error("FAILURE: IP was not rotated during identity rotation")
    
        if identity_rotated_session != session_rotated_session:
            logger.info("SUCCESS: Session was rotated during identity rotation")
        else:
            logger.error("FAILURE: Session was not rotated during identity rotation")
    
    # Clean up
        browser_manager.cleanup_user_resources(user_id)
    
        logger.info("Rotation test completed")

    def test_concurrent_sessions():
        """Test concurrent session functionality."""
        logger.info("Testing concurrent sessions...")
    
    # Use a queue to collect results from threads
        results_queue = Queue()
    
        def run_browser_session(user_id):
            """Run a browser session in a thread."""
            try:
                logger.info(f"Starting browser session for user {user_id}")
            
            # Setup browser
                driver = setup_browser(user_id)
            
                try:
                # Navigate to a test page
                    driver.get("https://www.whatismyip.com/")
                    time.sleep(5)
                
                # Get page title and URL
                    title = driver.title
                    url = driver.current_url
                
                # Try to extract IP (this is site-specific)
                    try:
                        ip_element = driver.find_element_by_id("ipv4")
                        ip = ip_element.text
                    except:
                        ip = "Could not extract IP"
                
                    results_queue.put({
                    "user_id": user_id,
                    "title": title,
                    "url": url,
                    "ip": ip,
                    "success": True
                })
                
                    logger.info(f"Browser session for user {user_id} completed")
                
                finally:
                # Close browser
                    driver.quit()
                
            except Exception as e:
                logger.error(f"Error in browser session for user {user_id}: {e}")
                results_queue.put({
                "user_id": user_id,
                "error": str(e),
                "success": False
            })
    
    # Start a thread for each test user
        threads = []
        for user_id in TEST_USERS:
            thread = threading.Thread(target=run_browser_session, args=(user_id,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
    
    # Wait for all threads to complete
        for thread in threads:
            thread.join()
    
    # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
    
    # Process results
        ips = {}
        for result in results:
            if result["success"]:
                logger.info(f"User {result['user_id']} browser session results:")
                logger.info(f"  Title: {result['title']}")
                logger.info(f"  URL: {result['url']}")
                logger.info(f"  IP: {result['ip']}")
            
                if "ip" in result:
                    ips[result["user_id"]] = result["ip"]
            else:
                logger.error(f"User {result['user_id']} browser session failed: {result['error']}")
    
    # Check if IPs are unique
        if len(set(ips.values())) == len(ips):
            logger.info("SUCCESS: All browser sessions had unique IPs")
        else:
            logger.error("FAILURE: Not all browser sessions had unique IPs")
    
        #

new_func()