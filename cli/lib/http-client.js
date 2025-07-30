const axios = require('axios');
const chalk = require('chalk');
const ora = require('ora');
const config = require('../config');

class HttpClient {
  constructor(serviceConfig) {
    this.baseURL = serviceConfig.url;
    this.timeout = serviceConfig.timeout || config.api.timeout;
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MCP-CLI/1.0.0'
      }
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        if (process.env.DEBUG) {
          console.log(chalk.gray(`→ ${config.method.toUpperCase()} ${config.url}`));
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        if (process.env.DEBUG) {
          console.log(chalk.gray(`← ${response.status} ${response.config.url}`));
        }
        return response;
      },
      (error) => {
        if (error.response) {
          // Server responded with error status
          const status = error.response.status;
          const message = error.response.data?.detail || error.response.data?.message || error.message;
          throw new Error(`HTTP ${status}: ${message}`);
        } else if (error.request) {
          // Request was made but no response received
          throw new Error(`Service unavailable: ${this.baseURL}`);
        } else {
          // Something else happened
          throw new Error(`Request failed: ${error.message}`);
        }
      }
    );
  }

  async get(path, options = {}) {
    return this.client.get(path, options);
  }

  async post(path, data, options = {}) {
    return this.client.post(path, data, options);
  }

  async put(path, data, options = {}) {
    return this.client.put(path, data, options);
  }

  async delete(path, options = {}) {
    return this.client.delete(path, options);
  }

  async healthCheck() {
    try {
      const response = await this.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  }
}

// Helper function to create client with spinner
function withSpinner(message, asyncFn) {
  return async (...args) => {
    const spinner = ora(message).start();
    try {
      const result = await asyncFn(...args);
      spinner.succeed();
      return result;
    } catch (error) {
      spinner.fail(error.message);
      throw error;
    }
  };
}

module.exports = { HttpClient, withSpinner };