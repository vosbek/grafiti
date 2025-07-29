package com.legacybank.web;

import com.legacybank.account.AccountService;
import com.legacybank.common.ValidationException;
import com.legacybank.model.Customer;
import com.legacybank.security.SecurityContext;
import com.legacybank.service.CustomerService;
import com.legacybank.validation.LoginValidator;

import org.apache.struts.action.Action;
import org.apache.struts.action.ActionForm;
import org.apache.struts.action.ActionForward;
import org.apache.struts.action.ActionMapping;
import org.apache.struts.action.ActionMessage;
import org.apache.struts.action.ActionMessages;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.util.Date;
import java.util.logging.Logger;

/**
 * Struts Action for handling customer login and authentication.
 * 
 * Security Requirements:
 * - Multi-factor authentication mandatory
 * - Account lockout after 3 failed attempts
 * - Session timeout after 15 minutes of inactivity
 * - IP address validation and logging
 * - Password complexity validation
 * 
 * Compliance:
 * - All login attempts logged for audit (SOX compliance)
 * - Failed login monitoring for fraud detection
 * - Customer identification verification (BSA compliance)
 */
public class LoginAction extends Action {
    
    private static final Logger logger = Logger.getLogger(LoginAction.class.getName());
    
    // Security constants
    private static final int MAX_LOGIN_ATTEMPTS = 3;
    private static final int SESSION_TIMEOUT_MINUTES = 15;
    private static final int ACCOUNT_LOCKOUT_DURATION_MINUTES = 30;
    
    private AccountService accountService;
    private CustomerService customerService;
    private LoginValidator loginValidator;
    private SecurityContext securityContext;
    
    /**
     * Main execute method for login action.
     * 
     * Business Rules:
     * - Customer ID and password are mandatory
     * - MFA token required for high-risk customers
     * - Account lockout after failed attempts
     * - Session establishment with security attributes
     */
    @Override
    public ActionForward execute(ActionMapping mapping, ActionForm form,
                               HttpServletRequest request, HttpServletResponse response) 
                               throws Exception {
        
        logger.info("Login attempt from IP: " + request.getRemoteAddr());
        
        LoginForm loginForm = (LoginForm) form;
        ActionMessages errors = new ActionMessages();
        
        try {
            // Validate input parameters
            if (!validateLoginForm(loginForm, errors)) {
                saveErrors(request, errors);
                return mapping.findForward("input");
            }
            
            // Check for account lockout
            if (isAccountLocked(loginForm.getCustomerId())) {
                errors.add("login", new ActionMessage("error.account.locked"));
                saveErrors(request, errors);
                logSecurityEvent("ACCOUNT_LOCKED", loginForm.getCustomerId(), request);
                return mapping.findForward("input");
            }
            
            // Validate IP address and detect suspicious activity
            if (!validateIPAddress(request)) {
                errors.add("login", new ActionMessage("error.suspicious.activity"));
                saveErrors(request, errors);
                logSecurityEvent("SUSPICIOUS_IP", loginForm.getCustomerId(), request);
                return mapping.findForward("security");
            }
            
            // Authenticate customer credentials
            boolean authenticated = authenticateCustomer(loginForm, request);
            
            if (authenticated) {
                // Successful authentication
                return handleSuccessfulLogin(loginForm, request, response, mapping);
            } else {
                // Failed authentication
                return handleFailedLogin(loginForm, request, errors, mapping);
            }
            
        } catch (ValidationException ve) {
            logger.warning("Validation error during login: " + ve.getMessage());
            errors.add("login", new ActionMessage("error.validation", ve.getMessage()));
            saveErrors(request, errors);
            return mapping.findForward("input");
            
        } catch (Exception e) {
            logger.severe("Unexpected error during login: " + e.getMessage());
            errors.add("login", new ActionMessage("error.system.unavailable"));
            saveErrors(request, errors);
            return mapping.findForward("error");
        }
    }
    
    /**
     * Validates the login form data.
     * 
     * Validation Rules:
     * - Customer ID must be 8-12 characters
     * - Password must meet complexity requirements
     * - MFA token format validation
     */
    private boolean validateLoginForm(LoginForm loginForm, ActionMessages errors) {
        
        boolean isValid = true;
        
        // Validate customer ID
        if (loginForm.getCustomerId() == null || loginForm.getCustomerId().trim().isEmpty()) {
            errors.add("customerId", new ActionMessage("error.required", "Customer ID"));
            isValid = false;
        } else if (!loginValidator.isValidCustomerId(loginForm.getCustomerId())) {
            errors.add("customerId", new ActionMessage("error.invalid.customerid"));
            isValid = false;
        }
        
        // Validate password
        if (loginForm.getPassword() == null || loginForm.getPassword().trim().isEmpty()) {
            errors.add("password", new ActionMessage("error.required", "Password"));
            isValid = false;
        } else if (!loginValidator.isValidPasswordFormat(loginForm.getPassword())) {
            errors.add("password", new ActionMessage("error.password.complexity"));
            isValid = false;
        }
        
        // Validate MFA token if required
        if (isHighRiskCustomer(loginForm.getCustomerId())) {
            if (loginForm.getMfaToken() == null || loginForm.getMfaToken().trim().isEmpty()) {
                errors.add("mfaToken", new ActionMessage("error.required", "MFA Token"));
                isValid = false;
            } else if (!loginValidator.isValidMFATokenFormat(loginForm.getMfaToken())) {
                errors.add("mfaToken", new ActionMessage("error.invalid.mfa.token"));
                isValid = false;
            }
        }
        
        return isValid;
    }
    
    /**
     * Authenticates customer using multiple security layers.
     */
    private boolean authenticateCustomer(LoginForm loginForm, HttpServletRequest request) {
        
        String customerId = loginForm.getCustomerId();
        String password = loginForm.getPassword();
        String mfaToken = loginForm.getMfaToken();
        
        // Primary authentication
        boolean credentialsValid = accountService.authenticateCustomer(customerId, password, mfaToken);
        
        if (!credentialsValid) {
            incrementFailedAttempts(customerId);
            logSecurityEvent("FAILED_LOGIN", customerId, request);
            return false;
        }
        
        // Additional security checks
        if (!performAdditionalSecurityChecks(customerId, request)) {
            logSecurityEvent("ADDITIONAL_SECURITY_FAILED", customerId, request);
            return false;
        }
        
        // Reset failed attempts on successful login
        resetFailedAttempts(customerId);
        
        return true;
    }
    
    /**
     * Handles successful login and establishes secure session.
     */
    private ActionForward handleSuccessfulLogin(LoginForm loginForm, 
                                              HttpServletRequest request,
                                              HttpServletResponse response,
                                              ActionMapping mapping) throws Exception {
        
        String customerId = loginForm.getCustomerId();
        
        // Retrieve customer information
        Customer customer = customerService.getCustomerById(customerId);
        
        // Create secure session
        HttpSession session = request.getSession(true);
        session.setAttribute("customerId", customerId);
        session.setAttribute("customer", customer);
        session.setAttribute("loginTime", new Date());
        session.setAttribute("lastActivity", new Date());
        session.setAttribute("sessionId", session.getId());
        session.setMaxInactiveInterval(SESSION_TIMEOUT_MINUTES * 60);
        
        // Set security attributes
        session.setAttribute("isAuthenticated", true);
        session.setAttribute("authenticationLevel", determineAuthenticationLevel(customer));
        session.setAttribute("clientIPAddress", request.getRemoteAddr());
        
        // Log successful login
        logSecurityEvent("SUCCESSFUL_LOGIN", customerId, request);
        
        // Update customer last login
        customerService.updateLastLogin(customerId, new Date(), request.getRemoteAddr());
        
        // Check for required password change
        if (customer.isPasswordChangeRequired()) {
            return mapping.findForward("changePassword");
        }
        
        // Check for required terms acceptance
        if (customer.isTermsAcceptanceRequired()) {
            return mapping.findForward("acceptTerms");
        }
        
        // Redirect to appropriate landing page based on customer profile
        if (customer.isPremiumCustomer()) {
            return mapping.findForward("premiumDashboard");
        } else {
            return mapping.findForward("dashboard");
        }
    }
    
    /**
     * Handles failed login attempts with security measures.
     */
    private ActionForward handleFailedLogin(LoginForm loginForm,
                                          HttpServletRequest request,
                                          ActionMessages errors,
                                          ActionMapping mapping) {
        
        String customerId = loginForm.getCustomerId();
        int failedAttempts = getFailedAttempts(customerId);
        
        if (failedAttempts >= MAX_LOGIN_ATTEMPTS) {
            // Lock the account
            lockAccount(customerId);
            errors.add("login", new ActionMessage("error.account.locked.attempts"));
            logSecurityEvent("ACCOUNT_LOCKED_ATTEMPTS", customerId, request);
        } else {
            errors.add("login", new ActionMessage("error.invalid.credentials", 
                      (MAX_LOGIN_ATTEMPTS - failedAttempts)));
        }
        
        saveErrors(request, errors);
        return mapping.findForward("input");
    }
    
    // Security helper methods
    
    private boolean isHighRiskCustomer(String customerId) {
        // Determine if customer requires MFA based on profile and transaction history
        Customer customer = customerService.getCustomerById(customerId);
        return customer != null && (customer.isPremiumAccount() || 
                                   customer.hasHighValueTransactions() ||
                                   customer.hasRecentSuspiciousActivity());
    }
    
    private boolean isAccountLocked(String customerId) {
        return securityContext.isAccountLocked(customerId);
    }
    
    private boolean validateIPAddress(HttpServletRequest request) {
        String clientIP = request.getRemoteAddr();
        return securityContext.isValidIPAddress(clientIP);
    }
    
    private boolean performAdditionalSecurityChecks(String customerId, HttpServletRequest request) {
        
        // Device fingerprinting
        String userAgent = request.getHeader("User-Agent");
        if (!securityContext.isKnownDevice(customerId, userAgent)) {
            // New device detected - may require additional verification
            logger.info("New device detected for customer: " + customerId);
        }
        
        // Geolocation validation
        String clientIP = request.getRemoteAddr();
        if (!securityContext.isValidGeolocation(customerId, clientIP)) {
            logger.warning("Unusual geolocation for customer: " + customerId);
            return false;
        }
        
        // Time-based validation
        if (!securityContext.isValidLoginTime(customerId)) {
            logger.warning("Login attempt outside normal hours for customer: " + customerId);
            return false;
        }
        
        return true;
    }
    
    private void incrementFailedAttempts(String customerId) {
        securityContext.incrementFailedLoginAttempts(customerId);
    }
    
    private void resetFailedAttempts(String customerId) {
        securityContext.resetFailedLoginAttempts(customerId);
    }
    
    private int getFailedAttempts(String customerId) {
        return securityContext.getFailedLoginAttempts(customerId);
    }
    
    private void lockAccount(String customerId) {
        securityContext.lockAccount(customerId, ACCOUNT_LOCKOUT_DURATION_MINUTES);
    }
    
    private String determineAuthenticationLevel(Customer customer) {
        if (customer.isPremiumCustomer()) {
            return "HIGH";
        } else if (customer.hasHighValueTransactions()) {
            return "MEDIUM";
        } else {
            return "STANDARD";
        }
    }
    
    private void logSecurityEvent(String eventType, String customerId, HttpServletRequest request) {
        String clientIP = request.getRemoteAddr();
        String userAgent = request.getHeader("User-Agent");
        Date timestamp = new Date();
        
        logger.info(String.format("SECURITY_EVENT: %s | Customer: %s | IP: %s | UserAgent: %s | Time: %s",
                   eventType, customerId, clientIP, userAgent, timestamp));
        
        // Additional logging to security audit system
        securityContext.logSecurityEvent(eventType, customerId, clientIP, userAgent, timestamp);
    }
    
    // Dependency injection setters
    
    public void setAccountService(AccountService accountService) {
        this.accountService = accountService;
    }
    
    public void setCustomerService(CustomerService customerService) {
        this.customerService = customerService;
    }
    
    public void setLoginValidator(LoginValidator loginValidator) {
        this.loginValidator = loginValidator;
    }
    
    public void setSecurityContext(SecurityContext securityContext) {
        this.securityContext = securityContext;
    }
}