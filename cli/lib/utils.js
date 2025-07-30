const chalk = require('chalk');
const fs = require('fs');
const path = require('path');

/**
 * Format JSON output with proper colors
 */
function formatJson(obj) {
  return JSON.stringify(obj, null, 2)
    .replace(/"([^"]+)":/g, chalk.blue('"$1"') + ':')
    .replace(/: "([^"]+)"/g, ': ' + chalk.green('"$1"'))
    .replace(/: (\d+)/g, ': ' + chalk.yellow('$1'))
    .replace(/: (true|false)/g, ': ' + chalk.cyan('$1'));
}

/**
 * Print a formatted error message
 */
function printError(message, details = null) {
  console.error(chalk.red.bold('❌ Error: ') + chalk.red(message));
  
  if (details) {
    if (typeof details === 'object') {
      console.error(chalk.gray(JSON.stringify(details, null, 2)));
    } else {
      console.error(chalk.gray(details));
    }
  }
}

/**
 * Print a success message
 */
function printSuccess(message, details = null) {
  console.log(chalk.green.bold('✅ Success: ') + chalk.green(message));
  
  if (details) {
    if (typeof details === 'object') {
      console.log(chalk.gray(JSON.stringify(details, null, 2)));
    } else {
      console.log(chalk.gray(details));
    }
  }
}

/**
 * Print a warning message
 */
function printWarning(message) {
  console.warn(chalk.yellow.bold('⚠️  Warning: ') + chalk.yellow(message));
}

/**
 * Print an info message
 */
function printInfo(message) {
  console.log(chalk.blue.bold('ℹ️  Info: ') + chalk.blue(message));
}

/**
 * Format a timestamp
 */
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

/**
 * Format file size in human readable format
 */
function formatFileSize(bytes) {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Truncate text to specified length
 */
function truncateText(text, maxLength = 50) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Load configuration from file
 */
function loadConfig(configPath) {
  try {
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      return config;
    }
  } catch (error) {
    printWarning(`Failed to load config from ${configPath}: ${error.message}`);
  }
  return {};
}

/**
 * Save configuration to file
 */
function saveConfig(configPath, config) {
  try {
    const configDir = path.dirname(configPath);
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return true;
  } catch (error) {
    printError(`Failed to save config to ${configPath}`, error.message);
    return false;
  }
}

/**
 * Validate required fields in an object
 */
function validateRequiredFields(obj, requiredFields) {
  const missing = [];
  
  for (const field of requiredFields) {
    if (!obj[field] || (typeof obj[field] === 'string' && obj[field].trim() === '')) {
      missing.push(field);
    }
  }
  
  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(', ')}`);
  }
  
  return true;
}

/**
 * Sanitize input text
 */
function sanitizeInput(input) {
  if (typeof input !== 'string') return input;
  
  // Remove potential command injection characters
  return input.replace(/[;&|`$(){}[\]]/g, '');
}

/**
 * Check if a URL is valid
 */
function isValidUrl(string) {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
}

/**
 * Format duration in human readable format
 */
function formatDuration(milliseconds) {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry an async function with exponential backoff
 */
async function retryWithBackoff(fn, maxRetries = 3, baseDelay = 1000) {
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        throw error;
      }
      
      const delay = baseDelay * Math.pow(2, attempt - 1);
      printWarning(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await sleep(delay);
    }
  }
  
  throw lastError;
}

module.exports = {
  formatJson,
  printError,
  printSuccess,
  printWarning,
  printInfo,
  formatTimestamp,
  formatFileSize,
  truncateText,
  loadConfig,
  saveConfig,
  validateRequiredFields,
  sanitizeInput,
  isValidUrl,
  formatDuration,
  sleep,
  retryWithBackoff
};