"""
Ban Detection utilities for Travian Whispers application.
This module provides advanced detection mechanisms for identifying bans, CAPTCHAs,
and suspicious behavior that might indicate detection.
"""
import logging
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Initialize logger
logger = logging.getLogger(__name__)

class DetectionAnalyzer:
    """Analyzer for detection patterns and suspicious behavior."""
    
    # Common Travian ban/block patterns
    BAN_PATTERNS = [
        r"(?:account|ip).*?(?:ban|block|suspend)",
        r"violat(?:ed|ion).*?(?:rules|terms)",
        r"multiple.*?accounts",
        r"suspicious.*?activity",
        r"security.*?measure"
    ]
    
    # Phrases that indicate a ban (case insensitive)
    BAN_PHRASES = [
        "account has been banned",
        "account has been suspended",
        "violation of the terms",
        "our system has detected",
        "suspicious activity",
        "your ip address has been blocked",
        "access denied",
        "multiple accounts detected"
    ]
    
    # URLs that might indicate ban/restriction
    RESTRICTED_URLS = [
        "banned", "suspended", "blocked", "violation", "security", "captcha"
    ]
    
    def __init__(self):
        """Initialize DetectionAnalyzer."""
        self.detection_history = {}
    
    def analyze_page(self, driver):
        """
        Analyze the current page for signs of detection or bans.
        
        Args:
            driver: Selenium WebDriver instance
            
        Returns:
            dict: Analysis results
        """
        results = {
            "is_banned": False,
            "is_captcha": False,
            "is_suspicious": False,
            "confidence": 0,
            "reason": None,
            "evidence": [],
            "risk_level": "low"
        }
        
        try:
            # Get current URL and page content
            current_url = driver.current_url
            page_source = driver.page_source
            
            # Check for CAPTCHA
            if self._check_for_captcha(driver, current_url, page_source):
                results["is_captcha"] = True
                results["confidence"] = 95
                results["reason"] = "CAPTCHA detected"
                results["risk_level"] = "medium"
                results["evidence"].append("CAPTCHA elements found on page")
            
            # Check for ban indicators
            ban_check = self._check_for_ban(driver, current_url, page_source)
            if ban_check.get("is_banned", False):
                results["is_banned"] = True
                results["confidence"] = ban_check.get("confidence", 80)
                results["reason"] = ban_check.get("reason", "Ban detected")
                results["risk_level"] = "high"
                results["evidence"].extend(ban_check.get("evidence", []))
            
            # Check for suspicious patterns
            suspicious_check = self._check_for_suspicious(driver, current_url, page_source)
            if suspicious_check.get("is_suspicious", False):
                results["is_suspicious"] = True
                
                # Update confidence if higher
                if suspicious_check.get("confidence", 0) > results["confidence"]:
                    results["confidence"] = suspicious_check.get("confidence", 60)
                    
                if not results["reason"]:
                    results["reason"] = suspicious_check.get("reason", "Suspicious behavior detected")
                    
                if suspicious_check.get("risk_level", "low") == "medium" and results["risk_level"] == "low":
                    results["risk_level"] = "medium"
                    
                results["evidence"].extend(suspicious_check.get("evidence", []))
        
        except Exception as e:
            logger.error(f"Error analyzing page: {e}")
            results["is_suspicious"] = True
            results["confidence"] = 30
            results["reason"] = f"Error during analysis: {str(e)}"
            results["evidence"].append("Exception during analysis")
        
        return results
    
    def _check_for_captcha(self, driver, current_url, page_source):
        """
        Check for CAPTCHA indicators.
        
        Args:
            driver: Selenium WebDriver instance
            current_url: Current page URL
            page_source: HTML source of the page
            
        Returns:
            bool: True if CAPTCHA is detected
        """
        # Check for common CAPTCHA elements
        captcha_indicators = [
            # Google reCAPTCHA
            "g-recaptcha",
            "recaptcha-checkbox",
            "recaptcha-anchor",
            # hCaptcha
            "h-captcha",
            "hcaptcha",
            # General
            "captcha-challenge",
            "captcha-container",
            "captcha-image"
        ]
        
        # Check URL for captcha mentions
        if "captcha" in current_url.lower():
            return True
        
        # Check page source for captcha indicators
        for indicator in captcha_indicators:
            if indicator in page_source:
                return True
        
        # Try to find elements directly
        try:
            captcha_selectors = [
                By.CLASS_NAME, "g-recaptcha",
                By.CLASS_NAME, "recaptcha-checkbox",
                By.CLASS_NAME, "h-captcha",
                By.ID, "captcha",
                By.XPATH, "//iframe[contains(@src, 'recaptcha')]",
                By.XPATH, "//iframe[contains(@src, 'hcaptcha')]"
            ]
            
            for i in range(0, len(captcha_selectors), 2):
                try:
                    element = driver.find_element(captcha_selectors[i], captcha_selectors[i+1])
                    if element:
                        return True
                except NoSuchElementException:
                    pass
        except Exception as e:
            logger.debug(f"Error checking for CAPTCHA elements: {e}")
        
        return False
    
    def _check_for_ban(self, driver, current_url, page_source):
        """
        Check for ban indicators.
        
        Args:
            driver: Selenium WebDriver instance
            current_url: Current page URL
            page_source: HTML source of the page
            
        Returns:
            dict: Ban check results
        """
        results = {
            "is_banned": False,
            "confidence": 0,
            "reason": None,
            "evidence": []
        }
        
        # Check URL for restricted patterns
        for pattern in self.RESTRICTED_URLS:
            if pattern in current_url.lower():
                results["is_banned"] = True
                results["confidence"] = 70
                results["reason"] = f"Restricted URL pattern: {pattern}"
                results["evidence"].append(f"Restricted URL: {current_url}")
                break
        
        # Check for ban phrases in text
        page_text = BeautifulSoup(page_source, "html.parser").get_text().lower()
        for phrase in self.BAN_PHRASES:
            if phrase.lower() in page_text:
                results["is_banned"] = True
                results["confidence"] = 90
                results["reason"] = f"Ban phrase detected: {phrase}"
                results["evidence"].append(f"Text contains ban phrase: {phrase}")
                break
        
        # Check for regex patterns
        for pattern in self.BAN_PATTERNS:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                results["is_banned"] = True
                results["confidence"] = 80
                results["reason"] = f"Ban pattern detected: {matches[0]}"
                results["evidence"].append(f"Text matches ban pattern: {matches[0]}")
                break
        
        # Check for common ban indicators in elements
        ban_indicators = [
            "//div[contains(text(), 'banned')]",
            "//div[contains(text(), 'suspended')]",
            "//div[contains(text(), 'blocked')]",
            "//div[contains(text(), 'violation')]",
            "//div[contains(text(), 'account has been')]",
            "//p[contains(text(), 'banned')]",
            "//p[contains(text(), 'suspended')]",
            "//h1[contains(text(), 'Access Denied')]",
            "//h2[contains(text(), 'Access Denied')]"
        ]
        
        for xpath in ban_indicators:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    results["is_banned"] = True
                    results["confidence"] = 95
                    results["reason"] = f"Ban element detected: {elements[0].text}"
                    results["evidence"].append(f"Element with ban text: {elements[0].text}")
                    break
            except Exception as e:
                logger.debug(f"Error checking ban element {xpath}: {e}")
        
        return results
    
    def _check_for_suspicious(self, driver, current_url, page_source):
        """
        Check for suspicious behavior indicators.
        
        Args:
            driver: Selenium WebDriver instance
            current_url: Current page URL
            page_source: HTML source of the page
            
        Returns:
            dict: Suspicious behavior check results
        """
        results = {
            "is_suspicious": False,
            "confidence": 0,
            "reason": None,
            "risk_level": "low",
            "evidence": []
        }
        
        # Check for unexpected redirects
        if "login" in current_url and "travian" not in current_url:
            results["is_suspicious"] = True
            results["confidence"] = 60
            results["reason"] = "Unexpected redirect to non-Travian login page"
            results["risk_level"] = "medium"
            results["evidence"].append(f"Redirected to: {current_url}")
        
        # Check for warning messages
        warning_xpaths = [
            "//div[contains(@class, 'warning')]",
            "//div[contains(@class, 'alert')]",
            "//div[contains(@class, 'error')]",
            "//p[contains(@class, 'warning')]"
        ]
        
        for xpath in warning_xpaths:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for element in elements:
                    text = element.text.lower()
                    if any(word in text for word in ["warning", "security", "suspicious", "unusual", "detected"]):
                        results["is_suspicious"] = True
                        results["confidence"] = 70
                        results["reason"] = f"Warning message detected: {element.text}"
                        results["risk_level"] = "medium"
                        results["evidence"].append(f"Warning element: {element.text}")
                        break
            except Exception as e:
                logger.debug(f"Error checking warning element {xpath}: {e}")
        
        # Check for JavaScript behavior
        try:
            # Check for fingerprinting scripts
            fingerprinting_indicators = [
                "canvas.toDataURL", 
                "navigator.userAgent", 
                "navigator.platform",
                "navigator.plugins",
                "screen.width",
                "screen.height"
            ]
            
            js_check = """
            return {
                hasFingerprinting: (function() {
                    var scripts = document.getElementsByTagName('script');
                    for (var i = 0; i < scripts.length; i++) {
                        var content = scripts[i].textContent || scripts[i].innerText || '';
                        if (%(indicators)s) {
                            return true;
                        }
                    }
                    return false;
                })()
            }
            """ % {"indicators": " || ".join([f"content.includes('{ind}')" for ind in fingerprinting_indicators])}
            
            result = driver.execute_script(js_check)
            
            if result.get("hasFingerprinting", False):
                results["is_suspicious"] = True
                results["confidence"] = 50
                results["reason"] = "Fingerprinting scripts detected"
                results["evidence"].append("Page contains fingerprinting JavaScript")
        except Exception as e:
            logger.debug(f"Error checking JavaScript behavior: {e}")
        
        return results
    
    def track_detection_event(self, user_id, event_type, context=None):
        """
        Track a detection event for a user.
        
        Args:
            user_id (str): User ID
            event_type (str): Type of event (captcha, ban, suspicious)
            context (dict, optional): Additional context about the event
            
        Returns:
            dict: Updated detection history for the user
        """
        if user_id not in self.detection_history:
            self.detection_history[user_id] = {
                "events": [],
                "risk_score": 0
            }
        
        # Record the event
        event = {
            "timestamp": datetime.utcnow(),
            "type": event_type,
            "context": context or {}
        }
        
        self.detection_history[user_id]["events"].append(event)
        
        # Calculate risk score based on events
        risk_score = 0
        
        # Consider only events from the last 24 hours
        recent_events = [e for e in self.detection_history[user_id]["events"] 
                         if (datetime.utcnow() - e["timestamp"]).total_seconds() < 86400]
        
        for event in recent_events:
            if event["type"] == "ban":
                risk_score += 50
            elif event["type"] == "captcha":
                risk_score += 20
            elif event["type"] == "suspicious":
                risk_score += 10
        
        # Cap risk score at 100
        risk_score = min(risk_score, 100)
        
        # Update risk score
        self.detection_history[user_id]["risk_score"] = risk_score
        
        # Determine risk level
        risk_level = "low"
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        
        self.detection_history[user_id]["risk_level"] = risk_level
        
        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "event_count": len(recent_events)
        }
    
    def get_user_risk_level(self, user_id):
        """
        Get the current risk level for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            str: Risk level (low, medium, high)
        """
        if user_id not in self.detection_history:
            return "low"
        
        return self.detection_history[user_id].get("risk_level", "low")
    
    def clear_user_history(self, user_id):
        """
        Clear detection history for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if history was cleared, False if user not found
        """
        if user_id in self.detection_history:
            del self.detection_history[user_id]
            return True
        return False


class DetectionHandler:
    """Handler for detection events with recovery strategies."""
    
    def __init__(self):
        """Initialize DetectionHandler."""
        self.analyzer = DetectionAnalyzer()
        
        # Initialize managers as needed
        from startup.session_isolation import BrowserIsolationManager
        self.browser_manager = BrowserIsolationManager()
    
    def check_detection(self, driver, user_id=None):
        """
        Check for any detection indicators on the current page.
        
        Args:
            driver: Selenium WebDriver instance
            user_id (str, optional): User ID for tracking
            
        Returns:
            dict: Detection analysis results
        """
        # Analyze the current page
        results = self.analyzer.analyze_page(driver)
        
        # Track the event if user_id is provided and there's something to track
        if user_id and (results["is_banned"] or results["is_captcha"] or results["is_suspicious"]):
            event_type = "ban" if results["is_banned"] else ("captcha" if results["is_captcha"] else "suspicious")
            context = {
                "url": driver.current_url,
                "reason": results["reason"],
                "confidence": results["confidence"]
            }
            
            self.analyzer.track_detection_event(user_id, event_type, context)
        
        return results
    
    def handle_detection(self, driver, user_id, results=None):
        """
        Handle a detection event with appropriate action.
        
        Args:
            driver: Selenium WebDriver instance
            user_id (str): User ID
            results (dict, optional): Detection results if already analyzed
            
        Returns:
            dict: Action taken
        """
        # Get detection results if not provided
        if results is None:
            results = self.check_detection(driver, user_id)
        
        risk_level = results.get("risk_level", "low")
        
        # Get current user risk level from history
        user_risk_level = self.analyzer.get_user_risk_level(user_id)
        
        # Use the higher risk level
        if user_risk_level == "high" or risk_level == "high":
            final_risk_level = "high"
        elif user_risk_level == "medium" or risk_level == "medium":
            final_risk_level = "medium"
        else:
            final_risk_level = "low"
        
        # Take action based on risk level
        action_result = self.browser_manager.handle_detection_risk(user_id, final_risk_level, results)
        
        # Log the action
        if final_risk_level != "low":
            logger.warning(f"Detection handled for user {user_id}: {results['reason']} (Risk level: {final_risk_level})")
            logger.info(f"Action taken: {action_result['action']}")
        
        return {
            "detection": results,
            "risk_level": final_risk_level,
            "action": action_result
        }
    
    def handle_captcha(self, driver, user_id):
        """
        Handle a CAPTCHA detection.
        
        Args:
            driver: Selenium WebDriver instance
            user_id (str): User ID
            
        Returns:
            dict: Action taken
        """
        results = {
            "is_captcha": True,
            "is_banned": False,
            "is_suspicious": False,
            "confidence": 95,
            "reason": "CAPTCHA detected",
            "risk_level": "medium",
            "evidence": ["CAPTCHA detected directly"]
        }
        
        # Track the event
        self.analyzer.track_detection_event(user_id, "captcha", {"url": driver.current_url})
        
        # Handle the detection
        return self.handle_detection(driver, user_id, results)
    
    def handle_ban(self, driver, user_id, ban_reason=None):
        """
        Handle a ban detection.
        
        Args:
            driver: Selenium WebDriver instance
            user_id (str): User ID
            ban_reason (str, optional): Ban reason if known
            
        Returns:
            dict: Action taken
        """
        results = {
            "is_captcha": False,
            "is_banned": True,
            "is_suspicious": False,
            "confidence": 95,
            "reason": ban_reason or "Ban detected",
            "risk_level": "high",
            "evidence": ["Ban detected directly"]
        }
        
        # Track the event
        self.analyzer.track_detection_event(user_id, "ban", {"url": driver.current_url, "reason": ban_reason})
        
        # Handle the detection
        return self.handle_detection(driver, user_id, results)
    
    def handle_suspicious(self, driver, user_id, details=None):
        """
        Handle a suspicious activity detection.
        
        Args:
            driver: Selenium WebDriver instance
            user_id (str): User ID
            details (dict, optional): Suspicious activity details
            
        Returns:
            dict: Action taken
        """
        results = {
            "is_captcha": False,
            "is_banned": False,
            "is_suspicious": True,
            "confidence": 70,
            "reason": "Suspicious activity detected",
            "risk_level": "medium",
            "evidence": ["Suspicious activity reported manually"]
        }
        
        if details:
            results["evidence"].append(f"Details: {details}")
        
        # Track the event
        self.analyzer.track_detection_event(user_id, "suspicious", {"url": driver.current_url, "details": details})
        
        # Handle the detection
        return self.handle_detection(driver, user_id, results)


# Create singleton instances
detection_analyzer = DetectionAnalyzer()
detection_handler = DetectionHandler()
