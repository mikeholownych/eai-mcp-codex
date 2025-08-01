#!/usr/bin/env node

/**
 * MCP Agent Network Frontend Performance Benchmark Tool
 * 
 * This script performs comprehensive performance testing including:
 * - Lighthouse audits
 * - Load testing with artillery
 * - Bundle analysis
 * - Core Web Vitals measurement
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');

// Configuration
const CONFIG = {
  baseUrl: process.env.TEST_URL || 'http://192.168.2.185',
  port: process.env.TEST_PORT || '80',
  outputDir: './performance-reports',
  lighthouse: {
    flags: {
      chromeFlags: ['--headless', '--no-sandbox', '--disable-dev-shm-usage'],
      output: 'html',
      onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    }
  },
  loadTest: {
    duration: '2m',
    arrivalRate: 10,
    maxVusers: 50
  }
};

// Test URLs to benchmark
const TEST_URLS = [
  '/',
  '/demo',
  '/blog', 
  '/docs',
  '/dashboard',
  '/chat',
  '/code-editor'
];

class PerformanceBenchmark {
  constructor() {
    this.results = {
      timestamp: new Date().toISOString(),
      environment: {
        url: `${CONFIG.baseUrl}:${CONFIG.port}`,
        node_version: process.version,
        platform: process.platform
      },
      lighthouse: {},
      loadTest: {},
      bundleAnalysis: {},
      webVitals: {}
    };
  }

  async run() {
    console.log('🚀 Starting MCP Frontend Performance Benchmark');
    console.log(`Testing URL: ${CONFIG.baseUrl}:${CONFIG.port}`);
    
    try {
      await this.ensureOutputDir();
      
      // Run all performance tests
      await this.runLighthouseAudits();
      await this.runBundleAnalysis();
      await this.runLoadTests();
      await this.measureWebVitals();
      
      // Generate comprehensive report
      await this.generateReport();
      
      console.log('✅ Performance benchmark completed successfully!');
      console.log(`📊 Reports saved to: ${CONFIG.outputDir}`);
      
    } catch (error) {
      console.error('❌ Benchmark failed:', error.message);
      process.exit(1);
    }
  }

  async ensureOutputDir() {
    try {
      await fs.mkdir(CONFIG.outputDir, { recursive: true });
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
    }
  }

  async runLighthouseAudits() {
    console.log('\n📊 Running Lighthouse audits...');
    
    const chrome = await chromeLauncher.launch({
      chromeFlags: CONFIG.lighthouse.flags.chromeFlags
    });
    
    try {
      for (const urlPath of TEST_URLS) {
        const url = `${CONFIG.baseUrl}:${CONFIG.port}${urlPath}`;
        console.log(`  Auditing: ${url}`);
        
        const runnerResult = await lighthouse(url, {
          ...CONFIG.lighthouse.flags,
          port: chrome.port,
        });
        
        // Extract key metrics
        const { lhr } = runnerResult;
        const metrics = {
          url: urlPath,
          score: lhr.categories.performance.score * 100,
          metrics: {
            'first-contentful-paint': lhr.audits['first-contentful-paint'].numericValue,
            'largest-contentful-paint': lhr.audits['largest-contentful-paint'].numericValue,
            'first-input-delay': lhr.audits['max-potential-fid'].numericValue,
            'cumulative-layout-shift': lhr.audits['cumulative-layout-shift'].numericValue,
            'time-to-interactive': lhr.audits['interactive'].numericValue,
            'speed-index': lhr.audits['speed-index'].numericValue
          },
          opportunities: lhr.audits['unused-css-rules']?.details?.items?.length || 0,
          diagnostics: {
            'render-blocking-resources': lhr.audits['render-blocking-resources']?.details?.items?.length || 0,
            'unused-javascript': lhr.audits['unused-javascript']?.details?.items?.length || 0
          }
        };
        
        this.results.lighthouse[urlPath] = metrics;
        
        // Save detailed report
        const reportPath = path.join(CONFIG.outputDir, `lighthouse-${urlPath.replace(/\//g, '_')}.html`);
        await fs.writeFile(reportPath, runnerResult.report);
      }
    } finally {
      await chrome.kill();
    }
  }

  async runBundleAnalysis() {
    console.log('\n📦 Analyzing bundle sizes...');
    
    try {
      // Get build directory info
      const buildDir = path.join(process.cwd(), 'frontend/.next');
      const staticDir = path.join(buildDir, 'static');
      
      if (await this.pathExists(staticDir)) {
        const bundleInfo = await this.analyzeBundleDirectory(staticDir);
        this.results.bundleAnalysis = bundleInfo;
        
        console.log('  Bundle analysis completed');
        console.log(`  Total JS size: ${(bundleInfo.totalSize / 1024).toFixed(2)} KB`);
        console.log(`  Number of chunks: ${bundleInfo.chunkCount}`);
      } else {
        console.log('  Build directory not found, skipping bundle analysis');
      }
    } catch (error) {
      console.log(`  Bundle analysis failed: ${error.message}`);
      this.results.bundleAnalysis = { error: error.message };
    }
  }

  async analyzeBundleDirectory(dir) {
    const files = await fs.readdir(dir, { recursive: true });
    const jsFiles = files.filter(file => file.endsWith('.js'));
    
    let totalSize = 0;
    const chunks = {};
    
    for (const file of jsFiles) {
      const filePath = path.join(dir, file);
      const stats = await fs.stat(filePath);
      const size = stats.size;
      totalSize += size;
      
      chunks[file] = {
        size: size,
        gzipSize: await this.estimateGzipSize(filePath)
      };
    }
    
    return {
      totalSize,
      chunkCount: jsFiles.length,
      chunks,
      recommendations: this.getBundleRecommendations(totalSize, jsFiles.length)
    };
  }

  async estimateGzipSize(filePath) {
    try {
      const content = await fs.readFile(filePath);
      const zlib = require('zlib');
      const compressed = zlib.gzipSync(content);
      return compressed.length;
    } catch (error) {
      return 0;
    }
  }

  getBundleRecommendations(totalSize, chunkCount) {
    const recommendations = [];
    
    if (totalSize > 500 * 1024) {
      recommendations.push('Consider code splitting to reduce bundle size');
    }
    
    if (chunkCount < 3) {
      recommendations.push('Consider splitting vendor and app code');
    }
    
    if (totalSize > 1024 * 1024) {
      recommendations.push('Bundle size is quite large, implement lazy loading');
    }
    
    return recommendations;
  }

  async runLoadTests() {
    console.log('\n🔥 Running load tests...');
    
    const artilleryConfig = {
      config: {
        target: `${CONFIG.baseUrl}:${CONFIG.port}`,
        phases: [
          {
            duration: CONFIG.loadTest.duration,
            arrivalRate: CONFIG.loadTest.arrivalRate,
            maxVusers: CONFIG.loadTest.maxVusers
          }
        ],
        processor: './load-test-processor.js'
      },
      scenarios: [
        {
          name: 'Homepage Load Test',
          weight: 30,
          flow: [
            { get: { url: '/' } }
          ]
        },
        {
          name: 'Multi-page Navigation',
          weight: 40,
          flow: [
            { get: { url: '/' } },
            { get: { url: '/demo' } },
            { get: { url: '/docs' } }
          ]
        },
        {
          name: 'API Endpoints',
          weight: 30,
          flow: [
            { get: { url: '/api/health' } },
            { get: { url: '/status' } }
          ]
        }
      ]
    };
    
    try {
      const configPath = path.join(CONFIG.outputDir, 'artillery-config.yml');
      await fs.writeFile(configPath, JSON.stringify(artilleryConfig, null, 2));
      
      // Run artillery
      const artilleryResult = execSync(
        `npx artillery run ${configPath} --output ${path.join(CONFIG.outputDir, 'load-test-results.json')}`,
        { encoding: 'utf8', timeout: 300000 }
      );
      
      // Parse results
      const resultsPath = path.join(CONFIG.outputDir, 'load-test-results.json');
      if (await this.pathExists(resultsPath)) {
        const rawResults = await fs.readFile(resultsPath, 'utf8');
        const loadTestResults = JSON.parse(rawResults);
        
        this.results.loadTest = {
          summary: {
            scenarios: loadTestResults.aggregate.counters,
            latency: loadTestResults.aggregate.latency,
            rps: loadTestResults.aggregate.rates
          },
          recommendations: this.getLoadTestRecommendations(loadTestResults)
        };
      }
      
      console.log('  Load testing completed');
    } catch (error) {
      console.log(`  Load testing failed: ${error.message}`);
      this.results.loadTest = { error: error.message };
    }
  }

  getLoadTestRecommendations(results) {
    const recommendations = [];
    const { latency, rates } = results.aggregate;
    
    if (latency.p95 > 2000) {
      recommendations.push('95th percentile latency is high, consider optimizing slow endpoints');
    }
    
    if (rates && rates['http.request_rate'] < 50) {
      recommendations.push('Request rate is low, server may be able to handle more load');
    }
    
    if (results.aggregate.counters['http.codes.500'] > 0) {
      recommendations.push('Server errors detected, investigate application stability');
    }
    
    return recommendations;
  }

  async measureWebVitals() {
    console.log('\n⚡ Measuring Core Web Vitals...');
    
    // This would ideally use real user monitoring data
    // For now, we'll use the Lighthouse metrics as approximation
    const webVitalsData = {};
    
    for (const [path, data] of Object.entries(this.results.lighthouse)) {
      webVitalsData[path] = {
        lcp: data.metrics['largest-contentful-paint'],
        fid: data.metrics['first-input-delay'],
        cls: data.metrics['cumulative-layout-shift'],
        fcp: data.metrics['first-contentful-paint'],
        ttfb: data.metrics['time-to-interactive'] / 4, // Rough estimation
        grade: this.getWebVitalsGrade(data.metrics)
      };
    }
    
    this.results.webVitals = webVitalsData;
    console.log('  Web Vitals measurement completed');
  }

  getWebVitalsGrade(metrics) {
    const lcp = metrics['largest-contentful-paint'];
    const fid = metrics['first-input-delay'];
    const cls = metrics['cumulative-layout-shift'];
    
    let score = 0;
    
    // LCP scoring
    if (lcp <= 2500) score += 33;
    else if (lcp <= 4000) score += 20;
    
    // FID scoring
    if (fid <= 100) score += 33;
    else if (fid <= 300) score += 20;
    
    // CLS scoring
    if (cls <= 0.1) score += 34;
    else if (cls <= 0.25) score += 20;
    
    if (score >= 80) return 'GOOD';
    if (score >= 50) return 'NEEDS_IMPROVEMENT';
    return 'POOR';
  }

  async generateReport() {
    console.log('\n📋 Generating comprehensive report...');
    
    // Generate JSON report
    const jsonReportPath = path.join(CONFIG.outputDir, 'performance-report.json');
    await fs.writeFile(jsonReportPath, JSON.stringify(this.results, null, 2));
    
    // Generate HTML report
    const htmlReport = this.generateHtmlReport();
    const htmlReportPath = path.join(CONFIG.outputDir, 'performance-report.html');
    await fs.writeFile(htmlReportPath, htmlReport);
    
    // Generate summary
    this.printSummary();
  }

  generateHtmlReport() {
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Frontend Performance Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { border-bottom: 2px solid #e0e0e0; padding-bottom: 20px; margin-bottom: 30px; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .metric-label { font-size: 14px; color: #666; text-transform: uppercase; }
        .section { margin: 30px 0; }
        .grade-good { color: #28a745; }
        .grade-needs-improvement { color: #ffc107; }
        .grade-poor { color: #dc3545; }
        .recommendations { background: #e3f2fd; padding: 15px; border-radius: 6px; margin: 15px 0; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP Frontend Performance Report</h1>
            <p><strong>Generated:</strong> ${this.results.timestamp}</p>
            <p><strong>Environment:</strong> ${this.results.environment.url}</p>
        </div>

        <div class="section">
            <h2>📊 Performance Overview</h2>
            <div class="metric-grid">
                ${Object.entries(this.results.lighthouse).map(([path, data]) => `
                    <div class="metric-card">
                        <div class="metric-value">${Math.round(data.score)}</div>
                        <div class="metric-label">${path} Score</div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="section">
            <h2>⚡ Core Web Vitals</h2>
            <table>
                <thead>
                    <tr>
                        <th>Page</th>
                        <th>LCP (ms)</th>
                        <th>FID (ms)</th>
                        <th>CLS</th>
                        <th>Grade</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(this.results.webVitals).map(([path, vitals]) => `
                        <tr>
                            <td>${path}</td>
                            <td>${Math.round(vitals.lcp)}</td>
                            <td>${Math.round(vitals.fid)}</td>
                            <td>${vitals.cls.toFixed(3)}</td>
                            <td class="grade-${vitals.grade.toLowerCase().replace('_', '-')}">${vitals.grade}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>📦 Bundle Analysis</h2>
            ${this.results.bundleAnalysis.totalSize ? `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">${(this.results.bundleAnalysis.totalSize / 1024).toFixed(1)}KB</div>
                        <div class="metric-label">Total Bundle Size</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${this.results.bundleAnalysis.chunkCount}</div>
                        <div class="metric-label">Number of Chunks</div>
                    </div>
                </div>
                ${this.results.bundleAnalysis.recommendations?.length ? `
                    <div class="recommendations">
                        <h4>🔧 Bundle Recommendations</h4>
                        <ul>
                            ${this.results.bundleAnalysis.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            ` : '<p>Bundle analysis data not available</p>'}
        </div>

        <div class="section">
            <h2>🔥 Load Testing Results</h2>
            ${this.results.loadTest.summary ? `
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="metric-value">${this.results.loadTest.summary.latency?.median || 'N/A'}ms</div>
                        <div class="metric-label">Median Latency</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${this.results.loadTest.summary.latency?.p95 || 'N/A'}ms</div>
                        <div class="metric-label">95th Percentile</div>
                    </div>
                </div>
            ` : '<p>Load testing data not available</p>'}
        </div>

        <div class="section">
            <h2>🎯 Summary & Recommendations</h2>
            <div class="recommendations">
                <h4>Key Performance Insights</h4>
                <ul>
                    <li>Average Lighthouse Score: ${Object.values(this.results.lighthouse).reduce((sum, data) => sum + data.score, 0) / Object.keys(this.results.lighthouse).length}%</li>
                    <li>Pages Tested: ${Object.keys(this.results.lighthouse).length}</li>
                    <li>Performance Grade: ${this.getOverallGrade()}</li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
    `;
  }

  getOverallGrade() {
    const grades = Object.values(this.results.webVitals).map(v => v.grade);
    const goodCount = grades.filter(g => g === 'GOOD').length;
    const totalCount = grades.length;
    
    if (goodCount / totalCount >= 0.8) return 'EXCELLENT';
    if (goodCount / totalCount >= 0.6) return 'GOOD';
    if (goodCount / totalCount >= 0.4) return 'NEEDS IMPROVEMENT';
    return 'POOR';
  }

  printSummary() {
    console.log('\n📋 Performance Summary:');
    console.log('========================');
    
    Object.entries(this.results.lighthouse).forEach(([path, data]) => {
      console.log(`${path}: ${Math.round(data.score)}% (LCP: ${Math.round(data.metrics['largest-contentful-paint'])}ms)`);
    });
    
    console.log(`\n🎯 Overall Grade: ${this.getOverallGrade()}`);
    console.log(`📊 Reports available in: ${CONFIG.outputDir}`);
  }

  async pathExists(path) {
    try {
      await fs.access(path);
      return true;
    } catch {
      return false;
    }
  }
}

// CLI execution
if (require.main === module) {
  const benchmark = new PerformanceBenchmark();
  benchmark.run().catch(console.error);
}

module.exports = PerformanceBenchmark;