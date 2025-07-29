package com.legacybank.account;

import com.legacybank.common.ValidationException;
import com.legacybank.common.BusinessRuleException;
import com.legacybank.corba.BankingServicePOA;
import com.legacybank.dao.AccountDAO;
import com.legacybank.model.Account;
import com.legacybank.model.Transaction;
import com.legacybank.security.SecurityContext;
import com.legacybank.validation.AccountValidator;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;
import java.util.logging.Logger;

/**
 * Core banking service for account operations.
 * 
 * Business Rules:
 * - Minimum balance of $100 for checking accounts
 * - Maximum daily withdrawal limit of $5,000
 * - Account must be active for transactions
 * - Overdraft protection available for premium accounts
 * 
 * Compliance Requirements:
 * - All transactions must be logged for audit (SOX)
 * - Customer identification required for transactions > $10,000 (BSA)
 * - Interest calculations must follow federal banking guidelines
 */
@Service
@Transactional
public class AccountService extends BankingServicePOA {
    
    private static final Logger logger = Logger.getLogger(AccountService.class.getName());
    
    // Business rule constants
    private static final BigDecimal MINIMUM_CHECKING_BALANCE = new BigDecimal("100.00");
    private static final BigDecimal DAILY_WITHDRAWAL_LIMIT = new BigDecimal("5000.00");
    private static final BigDecimal HIGH_VALUE_TRANSACTION_THRESHOLD = new BigDecimal("10000.00");
    private static final BigDecimal OVERDRAFT_FEE = new BigDecimal("35.00");
    
    @Autowired
    private AccountDAO accountDAO;
    
    @Autowired
    private AccountValidator accountValidator;
    
    @Autowired
    private SecurityContext securityContext;
    
    /**
     * Creates a new bank account with comprehensive validation.
     * 
     * Business Rules:
     * - Customer must be 18 years or older
     * - Initial deposit must be at least $25
     * - SSN validation required
     * - Address verification needed
     */
    public Account createAccount(String customerId, String accountType, BigDecimal initialDeposit) 
            throws ValidationException, BusinessRuleException {
        
        logger.info("Creating new account for customer: " + customerId);
        
        // Validate customer eligibility
        if (!accountValidator.isEligibleCustomer(customerId)) {
            throw new ValidationException("Customer is not eligible for account opening");
        }
        
        // Validate initial deposit business rule
        if (initialDeposit.compareTo(new BigDecimal("25.00")) < 0) {
            throw new BusinessRuleException("Initial deposit must be at least $25.00");
        }
        
        // Apply account type specific rules
        if ("CHECKING".equals(accountType)) {
            validateCheckingAccountRules(initialDeposit);
        } else if ("SAVINGS".equals(accountType)) {
            validateSavingsAccountRules(initialDeposit);
        }
        
        Account account = new Account();
        account.setCustomerId(customerId);
        account.setAccountType(accountType);
        account.setBalance(initialDeposit);
        account.setStatus("ACTIVE");
        account.setCreatedDate(new Date());
        account.setCreatedBy(securityContext.getCurrentUser());
        
        return accountDAO.save(account);
    }
    
    /**
     * Processes account withdrawal with comprehensive business rule validation.
     * 
     * Business Rules:
     * - Sufficient funds must be available (or overdraft protection)
     * - Daily withdrawal limits enforced
     * - Account must be active
     * - High-value transactions require additional verification
     */
    public Transaction processWithdrawal(String accountNumber, BigDecimal amount, String description) 
            throws ValidationException, BusinessRuleException {
        
        logger.info("Processing withdrawal: " + accountNumber + " Amount: " + amount);
        
        Account account = getAccountByNumber(accountNumber);
        
        // Validate account status
        if (!"ACTIVE".equals(account.getStatus())) {
            throw new BusinessRuleException("Account must be active for transactions");
        }
        
        // Check daily withdrawal limit
        BigDecimal dailyWithdrawals = calculateDailyWithdrawals(accountNumber);
        if (dailyWithdrawals.add(amount).compareTo(DAILY_WITHDRAWAL_LIMIT) > 0) {
            throw new BusinessRuleException("Daily withdrawal limit of $5,000 exceeded");
        }
        
        // High-value transaction verification
        if (amount.compareTo(HIGH_VALUE_TRANSACTION_THRESHOLD) > 0) {
            if (!securityContext.isHighValueTransactionAuthorized()) {
                throw new ValidationException("Additional authorization required for high-value transactions");
            }
        }
        
        // Check sufficient funds and overdraft rules
        if (account.getBalance().compareTo(amount) < 0) {
            if (account.isOverdraftProtectionEnabled() && account.getOverdraftLimit().compareTo(amount.subtract(account.getBalance())) >= 0) {
                // Apply overdraft fee
                processOverdraftFee(account);
                logger.info("Overdraft protection applied for account: " + accountNumber);
            } else {
                throw new BusinessRuleException("Insufficient funds for withdrawal");
            }
        }
        
        // Process the withdrawal
        account.setBalance(account.getBalance().subtract(amount));
        accountDAO.update(account);
        
        // Create transaction record
        Transaction transaction = new Transaction();
        transaction.setAccountNumber(accountNumber);
        transaction.setTransactionType("WITHDRAWAL");
        transaction.setAmount(amount);
        transaction.setDescription(description);
        transaction.setTransactionDate(new Date());
        transaction.setProcessedBy(securityContext.getCurrentUser());
        
        return transaction;
    }
    
    /**
     * Calculates and applies interest based on account type and balance.
     * 
     * Business Rules:
     * - Checking accounts: 0.01% APY on balances > $1,000
     * - Savings accounts: 0.05% APY on all balances
     * - Premium accounts: Additional 0.02% bonus APY
     * - Interest compounded monthly
     */
    public void calculateInterest(String accountNumber) throws BusinessRuleException {
        
        Account account = getAccountByNumber(accountNumber);
        BigDecimal interestRate = determineInterestRate(account);
        
        if (interestRate.compareTo(BigDecimal.ZERO) > 0) {
            BigDecimal monthlyInterest = account.getBalance()
                .multiply(interestRate)
                .divide(new BigDecimal("12"), 2, BigDecimal.ROUND_HALF_UP);
            
            account.setBalance(account.getBalance().add(monthlyInterest));
            accountDAO.update(account);
            
            // Create interest transaction record
            Transaction interestTransaction = new Transaction();
            interestTransaction.setAccountNumber(accountNumber);
            interestTransaction.setTransactionType("INTEREST");
            interestTransaction.setAmount(monthlyInterest);
            interestTransaction.setDescription("Monthly interest payment");
            interestTransaction.setTransactionDate(new Date());
            interestTransaction.setProcessedBy("SYSTEM");
            
            logger.info("Interest applied to account " + accountNumber + ": $" + monthlyInterest);
        }
    }
    
    /**
     * Validates customer authentication for high-security operations.
     * 
     * Security Rules:
     * - Multi-factor authentication required
     * - Session timeout validation
     * - IP address verification
     * - Transaction pattern analysis
     */
    public boolean authenticateCustomer(String customerId, String password, String token) {
        
        // Validate session timeout
        if (securityContext.isSessionExpired()) {
            logger.warning("Session expired for customer: " + customerId);
            return false;
        }
        
        // Validate IP address
        if (!securityContext.isValidIPAddress()) {
            logger.warning("Invalid IP address for customer: " + customerId);
            return false;
        }
        
        // Multi-factor authentication
        if (!validateCredentials(customerId, password)) {
            logger.warning("Invalid credentials for customer: " + customerId);
            return false;
        }
        
        if (!validateMFAToken(customerId, token)) {
            logger.warning("Invalid MFA token for customer: " + customerId);
            return false;
        }
        
        // Check for suspicious transaction patterns
        if (detectSuspiciousActivity(customerId)) {
            logger.warning("Suspicious activity detected for customer: " + customerId);
            return false;
        }
        
        logger.info("Customer authenticated successfully: " + customerId);
        return true;
    }
    
    // Private helper methods
    
    private void validateCheckingAccountRules(BigDecimal initialDeposit) throws BusinessRuleException {
        if (initialDeposit.compareTo(MINIMUM_CHECKING_BALANCE) < 0) {
            throw new BusinessRuleException("Checking accounts require minimum deposit of $100.00");
        }
    }
    
    private void validateSavingsAccountRules(BigDecimal initialDeposit) throws BusinessRuleException {
        // Savings accounts have no minimum balance requirement
        // But we apply a different interest rate structure
    }
    
    private Account getAccountByNumber(String accountNumber) throws ValidationException {
        Account account = accountDAO.findByAccountNumber(accountNumber);
        if (account == null) {
            throw new ValidationException("Account not found: " + accountNumber);
        }
        return account;
    }
    
    private BigDecimal calculateDailyWithdrawals(String accountNumber) {
        List<Transaction> todaysWithdrawals = accountDAO.getTodaysWithdrawals(accountNumber);
        return todaysWithdrawals.stream()
            .map(Transaction::getAmount)
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
    
    private void processOverdraftFee(Account account) {
        account.setBalance(account.getBalance().subtract(OVERDRAFT_FEE));
        logger.info("Overdraft fee applied: $" + OVERDRAFT_FEE);
    }
    
    private BigDecimal determineInterestRate(Account account) {
        BigDecimal baseRate = BigDecimal.ZERO;
        
        switch (account.getAccountType()) {
            case "CHECKING":
                if (account.getBalance().compareTo(new BigDecimal("1000.00")) > 0) {
                    baseRate = new BigDecimal("0.0001"); // 0.01% APY
                }
                break;
            case "SAVINGS":
                baseRate = new BigDecimal("0.0005"); // 0.05% APY
                break;
        }
        
        // Premium account bonus
        if (account.isPremiumAccount()) {
            baseRate = baseRate.add(new BigDecimal("0.0002")); // Additional 0.02% APY
        }
        
        return baseRate;
    }
    
    private boolean validateCredentials(String customerId, String password) {
        // Credential validation logic
        return accountDAO.validateCustomerCredentials(customerId, password);
    }
    
    private boolean validateMFAToken(String customerId, String token) {
        // MFA token validation logic
        return securityContext.validateMFAToken(customerId, token);
    }
    
    private boolean detectSuspiciousActivity(String customerId) {
        // Fraud detection logic
        return securityContext.checkSuspiciousActivity(customerId);
    }
}