import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import chalk from 'chalk';
import ora from 'ora';
import config from '../config';

export class HttpClient {
  protected client: AxiosInstance;
  private baseURL: string;

  constructor(serviceConfig: { url: string; timeout?: number }) {
    this.baseURL = serviceConfig.url;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: serviceConfig.timeout || config.api.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'MCP-CLI/1.0.0'
      }
    });

    this.client.interceptors.request.use(
      (cfg) => {
        if (process.env.DEBUG) {
          console.log(chalk.gray(`→ ${cfg.method?.toUpperCase()} ${cfg.url}`));
        }
        return cfg;
      },
      (error) => Promise.reject(error)
    );

    this.client.interceptors.response.use(
      (response) => {
        if (process.env.DEBUG) {
          console.log(chalk.gray(`← ${response.status} ${response.config.url}`));
        }
        return response;
      },
      (error) => {
        if (error.response) {
          const status = error.response.status;
          const message = error.response.data?.detail || error.response.data?.message || error.message;
          throw new Error(`HTTP ${status}: ${message}`);
        } else if (error.request) {
          throw new Error(`Service unavailable: ${this.baseURL}`);
        }
        throw new Error(`Request failed: ${error.message}`);
      }
    );
  }

  async get<T = any>(path: string, options: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> {
    return this.client.get<T>(path, options);
  }

  async post<T = any>(path: string, data?: any, options: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> {
    return this.client.post<T>(path, data, options);
  }

  async put<T = any>(path: string, data?: any, options: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> {
    return this.client.put<T>(path, data, options);
  }

  async delete<T = any>(path: string, options: AxiosRequestConfig = {}): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(path, options);
  }

  async healthCheck(): Promise<any> {
    const res = await this.get('/health');
    return res.data;
  }
}

export function withSpinner<T>(message: string, fn: (...args: any[]) => Promise<T>) {
  return async (...args: Parameters<typeof fn>): Promise<T> => {
    const spinner = ora(message).start();
    try {
      const result = await fn(...args);
      spinner.succeed();
      return result;
    } catch (error: any) {
      spinner.fail(error.message);
      throw error;
    }
  };
}
