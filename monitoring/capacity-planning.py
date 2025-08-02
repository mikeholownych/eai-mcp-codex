#!/usr/bin/env python3
"""
Capacity Planning and Resource Trend Analysis for EAI-MCP Platform
Advanced predictive analytics for infrastructure scaling decisions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import aiohttp
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""

    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    gpu_usage: Optional[float] = None
    timestamp: datetime = None


@dataclass
class ServiceMetrics:
    """Service-specific performance metrics"""

    request_rate: float
    response_time_p95: float
    error_rate: float
    active_connections: int
    throughput: float
    timestamp: datetime = None


@dataclass
class CapacityPrediction:
    """Capacity planning prediction results"""

    service: str
    metric: str
    current_value: float
    predicted_value: float
    confidence_interval: Tuple[float, float]
    days_until_threshold: Optional[int]
    recommended_action: str
    urgency: str  # low, medium, high, critical


class MetricsCollector:
    """Collects metrics from Prometheus and other sources"""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def query_prometheus(
        self, query: str, start_time: datetime, end_time: datetime
    ) -> Dict:
        """Query Prometheus for metrics data"""
        params = {
            "query": query,
            "start": start_time.timestamp(),
            "end": end_time.timestamp(),
            "step": "300s",  # 5-minute intervals
        }

        try:
            async with self.session.get(
                f"{self.prometheus_url}/api/v1/query_range", params=params
            ) as response:
                data = await response.json()
                return data.get("data", {}).get("result", [])
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return []

    async def get_resource_metrics(
        self, lookback_days: int = 7
    ) -> List[ResourceMetrics]:
        """Collect resource utilization metrics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback_days)

        metrics = []

        # CPU Usage
        cpu_query = '100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        cpu_data = await self.query_prometheus(cpu_query, start_time, end_time)

        # Memory Usage
        memory_query = (
            "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
        )
        memory_data = await self.query_prometheus(memory_query, start_time, end_time)

        # Disk Usage
        disk_query = (
            "(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100"
        )
        disk_data = await self.query_prometheus(disk_query, start_time, end_time)

        # Network I/O
        network_query = "rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m])"
        network_data = await self.query_prometheus(network_query, start_time, end_time)

        # Combine metrics by timestamp
        timestamps = set()
        if cpu_data:
            timestamps.update(
                [float(point[0]) for point in cpu_data[0].get("values", [])]
            )

        for ts in sorted(timestamps):
            cpu_val = self._extract_value_at_time(cpu_data, ts)
            memory_val = self._extract_value_at_time(memory_data, ts)
            disk_val = self._extract_value_at_time(disk_data, ts)
            network_val = self._extract_value_at_time(network_data, ts)

            if all(v is not None for v in [cpu_val, memory_val, disk_val, network_val]):
                metrics.append(
                    ResourceMetrics(
                        cpu_usage=cpu_val,
                        memory_usage=memory_val,
                        disk_usage=disk_val,
                        network_io=network_val,
                        timestamp=datetime.fromtimestamp(ts),
                    )
                )

        return metrics

    async def get_service_metrics(
        self, service: str, lookback_days: int = 7
    ) -> List[ServiceMetrics]:
        """Collect service-specific performance metrics"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback_days)

        metrics = []

        # Request rate
        rate_query = f'rate(http_requests_total{{job="{service}"}}[5m])'
        rate_data = await self.query_prometheus(rate_query, start_time, end_time)

        # Response time P95
        latency_query = f'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{job="{service}"}}[5m]))'
        latency_data = await self.query_prometheus(latency_query, start_time, end_time)

        # Error rate
        error_query = f'rate(http_requests_total{{job="{service}",status=~"5.."}}[5m]) / rate(http_requests_total{{job="{service}"}}[5m])'
        error_data = await self.query_prometheus(error_query, start_time, end_time)

        # Active connections (if available)
        conn_query = f'http_connections_active{{job="{service}"}}'
        conn_data = await self.query_prometheus(conn_query, start_time, end_time)

        # Combine metrics by timestamp
        timestamps = set()
        if rate_data:
            timestamps.update(
                [float(point[0]) for point in rate_data[0].get("values", [])]
            )

        for ts in sorted(timestamps):
            rate_val = self._extract_value_at_time(rate_data, ts)
            latency_val = self._extract_value_at_time(latency_data, ts)
            error_val = self._extract_value_at_time(error_data, ts)
            conn_val = self._extract_value_at_time(conn_data, ts) or 0

            if all(v is not None for v in [rate_val, latency_val, error_val]):
                metrics.append(
                    ServiceMetrics(
                        request_rate=rate_val,
                        response_time_p95=latency_val,
                        error_rate=error_val,
                        active_connections=int(conn_val),
                        throughput=rate_val,  # Simplified throughput calculation
                        timestamp=datetime.fromtimestamp(ts),
                    )
                )

        return metrics

    def _extract_value_at_time(
        self, data: List[Dict], timestamp: float
    ) -> Optional[float]:
        """Extract metric value at specific timestamp"""
        if not data or not data[0].get("values"):
            return None

        values = data[0]["values"]
        for ts, value in values:
            if abs(float(ts) - timestamp) < 150:  # Within 2.5 minutes
                try:
                    return float(value)
                except (ValueError, TypeError):
                    pass
        return None


class TrendAnalyzer:
    """Analyzes trends and makes capacity predictions"""

    def __init__(self):
        self.models = {
            "linear": self._linear_regression,
            "exponential": self._exponential_regression,
            "seasonal": self._seasonal_decomposition,
        }

    def analyze_resource_trends(
        self, metrics: List[ResourceMetrics]
    ) -> Dict[str, CapacityPrediction]:
        """Analyze resource utilization trends"""
        if len(metrics) < 10:
            logger.warning("Insufficient data for trend analysis")
            return {}

        df = pd.DataFrame(
            [
                {
                    "timestamp": m.timestamp,
                    "cpu_usage": m.cpu_usage,
                    "memory_usage": m.memory_usage,
                    "disk_usage": m.disk_usage,
                    "network_io": m.network_io,
                }
                for m in metrics
            ]
        )

        df["timestamp_numeric"] = pd.to_numeric(df["timestamp"])

        predictions = {}

        # Analyze each resource metric
        for metric in ["cpu_usage", "memory_usage", "disk_usage"]:
            prediction = self._predict_capacity(
                df,
                metric,
                thresholds={
                    "cpu_usage": 80.0,
                    "memory_usage": 85.0,
                    "disk_usage": 90.0,
                }[metric],
            )
            predictions[metric] = prediction

        return predictions

    def analyze_service_trends(
        self, service: str, metrics: List[ServiceMetrics]
    ) -> Dict[str, CapacityPrediction]:
        """Analyze service performance trends"""
        if len(metrics) < 10:
            logger.warning(f"Insufficient data for {service} trend analysis")
            return {}

        df = pd.DataFrame(
            [
                {
                    "timestamp": m.timestamp,
                    "request_rate": m.request_rate,
                    "response_time_p95": m.response_time_p95,
                    "error_rate": m.error_rate,
                    "active_connections": m.active_connections,
                }
                for m in metrics
            ]
        )

        df["timestamp_numeric"] = pd.to_numeric(df["timestamp"])

        predictions = {}

        # Analyze service metrics
        thresholds = {
            "request_rate": self._calculate_dynamic_threshold(df["request_rate"]),
            "response_time_p95": 2.0,  # 2 second SLO
            "error_rate": 0.01,  # 1% error rate
            "active_connections": self._calculate_dynamic_threshold(
                df["active_connections"]
            ),
        }

        for metric in thresholds:
            prediction = self._predict_capacity(
                df, metric, thresholds[metric], service=service
            )
            predictions[f"{service}_{metric}"] = prediction

        return predictions

    def _predict_capacity(
        self, df: pd.DataFrame, metric: str, threshold: float, service: str = "system"
    ) -> CapacityPrediction:
        """Predict when a metric will reach threshold"""
        current_value = df[metric].iloc[-1]

        # Try different models and pick the best fit
        best_prediction = None
        best_score = float("inf")

        for model_name, model_func in self.models.items():
            try:
                prediction = model_func(df, metric, threshold)
                if prediction and prediction.get("score", float("inf")) < best_score:
                    best_prediction = prediction
                    best_score = prediction.get("score", float("inf"))
            except Exception as e:
                logger.debug(f"Model {model_name} failed for {metric}: {e}")

        if not best_prediction:
            # Fallback to simple linear trend
            best_prediction = self._simple_linear_prediction(df, metric, threshold)

        # Determine recommended action and urgency
        days_until_threshold = best_prediction.get("days_until_threshold")
        recommended_action, urgency = self._determine_action(
            metric, current_value, threshold, days_until_threshold
        )

        return CapacityPrediction(
            service=service,
            metric=metric,
            current_value=current_value,
            predicted_value=best_prediction.get("predicted_value", current_value),
            confidence_interval=best_prediction.get(
                "confidence_interval", (current_value, current_value)
            ),
            days_until_threshold=days_until_threshold,
            recommended_action=recommended_action,
            urgency=urgency,
        )

    def _linear_regression(
        self, df: pd.DataFrame, metric: str, threshold: float
    ) -> Dict:
        """Simple linear regression prediction"""
        from sklearn.linear_model import LinearRegression
        from sklearn.metrics import mean_squared_error

        X = df["timestamp_numeric"].values.reshape(-1, 1)
        y = df[metric].values

        model = LinearRegression()
        model.fit(X, y)

        # Predict future values
        last_timestamp = X[-1][0]
        future_days = 30
        future_timestamps = np.linspace(
            last_timestamp,
            last_timestamp + (future_days * 24 * 3600 * 1000000000),  # nanoseconds
            future_days,
        ).reshape(-1, 1)

        predictions = model.predict(future_timestamps)

        # Calculate when threshold will be reached
        days_until_threshold = None
        if model.coef_[0] > 0:  # Increasing trend
            for i, pred in enumerate(predictions):
                if pred >= threshold:
                    days_until_threshold = i + 1
                    break

        # Calculate confidence interval (simplified)
        y_pred = model.predict(X)
        mse = mean_squared_error(y, y_pred)
        std_error = np.sqrt(mse)

        return {
            "predicted_value": predictions[-1],
            "confidence_interval": (
                predictions[-1] - 1.96 * std_error,
                predictions[-1] + 1.96 * std_error,
            ),
            "days_until_threshold": days_until_threshold,
            "score": mse,
        }

    def _exponential_regression(
        self, df: pd.DataFrame, metric: str, threshold: float
    ) -> Dict:
        """Exponential growth/decay prediction"""
        # Simplified exponential fitting
        try:
            X = np.arange(len(df))
            y = df[metric].values

            # Fit exponential curve: y = a * exp(b * x) + c
            from scipy.optimize import curve_fit

            def exp_func(x, a, b, c):
                return a * np.exp(b * x) + c

            popt, _ = curve_fit(exp_func, X, y, maxfev=1000)

            # Predict future
            future_x = np.arange(len(df), len(df) + 30)
            predictions = exp_func(future_x, *popt)

            # Find threshold crossing
            days_until_threshold = None
            if popt[1] > 0:  # Growing exponentially
                for i, pred in enumerate(predictions):
                    if pred >= threshold:
                        days_until_threshold = i + 1
                        break

            return {
                "predicted_value": predictions[-1],
                "confidence_interval": (predictions[-1] * 0.8, predictions[-1] * 1.2),
                "days_until_threshold": days_until_threshold,
                "score": np.mean((exp_func(X, *popt) - y) ** 2),
            }
        except Exception:
            return None

    def _seasonal_decomposition(
        self, df: pd.DataFrame, metric: str, threshold: float
    ) -> Dict:
        """Seasonal trend decomposition"""
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose

            # Resample to daily frequency if needed
            df_resampled = df.set_index("timestamp").resample("D")[metric].mean()

            if len(df_resampled) < 14:  # Need at least 2 weeks
                return None

            decomposition = seasonal_decompose(df_resampled, model="additive", period=7)
            trend = decomposition.trend.dropna()

            if len(trend) < 7:
                return None

            # Simple linear extrapolation of trend
            X = np.arange(len(trend))
            y = trend.values

            # Fit linear trend
            coeffs = np.polyfit(X, y, 1)

            # Predict future trend
            future_days = 30
            future_x = np.arange(len(trend), len(trend) + future_days)
            future_trend = np.polyval(coeffs, future_x)

            # Add seasonal component (use average seasonal pattern)
            seasonal_avg = decomposition.seasonal.mean()
            predictions = future_trend + seasonal_avg

            # Find threshold crossing
            days_until_threshold = None
            if coeffs[0] > 0:  # Increasing trend
                for i, pred in enumerate(predictions):
                    if pred >= threshold:
                        days_until_threshold = i + 1
                        break

            return {
                "predicted_value": predictions[-1],
                "confidence_interval": (predictions[-1] * 0.9, predictions[-1] * 1.1),
                "days_until_threshold": days_until_threshold,
                "score": np.mean((np.polyval(coeffs, X) - y) ** 2),
            }
        except Exception:
            return None

    def _simple_linear_prediction(
        self, df: pd.DataFrame, metric: str, threshold: float
    ) -> Dict:
        """Fallback simple linear prediction"""
        values = df[metric].values
        if len(values) < 2:
            return {
                "predicted_value": values[-1],
                "confidence_interval": (values[-1], values[-1]),
                "days_until_threshold": None,
            }

        # Calculate simple slope
        recent_values = values[-7:]  # Last week
        slope = (recent_values[-1] - recent_values[0]) / len(recent_values)

        current_value = values[-1]
        future_value = current_value + (slope * 30)  # 30 days ahead

        days_until_threshold = None
        if slope > 0 and current_value < threshold:
            days_until_threshold = int((threshold - current_value) / slope)

        return {
            "predicted_value": future_value,
            "confidence_interval": (future_value * 0.8, future_value * 1.2),
            "days_until_threshold": days_until_threshold,
        }

    def _calculate_dynamic_threshold(self, series: pd.Series) -> float:
        """Calculate dynamic threshold based on historical data"""
        return series.quantile(0.95)  # 95th percentile as threshold

    def _determine_action(
        self, metric: str, current: float, threshold: float, days_until: Optional[int]
    ) -> Tuple[str, str]:
        """Determine recommended action and urgency level"""
        current_utilization = current / threshold if threshold > 0 else 0

        # Base recommendations by metric type
        actions = {
            "cpu_usage": {
                "scale_up": "Scale up CPU resources or add more instances",
                "optimize": "Optimize CPU-intensive operations",
                "monitor": "Continue monitoring CPU usage trends",
            },
            "memory_usage": {
                "scale_up": "Increase memory allocation or add more instances",
                "optimize": "Investigate memory leaks and optimize memory usage",
                "monitor": "Continue monitoring memory usage patterns",
            },
            "disk_usage": {
                "scale_up": "Add more storage capacity or implement data archiving",
                "optimize": "Clean up temporary files and implement log rotation",
                "monitor": "Monitor disk usage growth and plan expansion",
            },
            "response_time_p95": {
                "scale_up": "Scale up service instances or optimize performance",
                "optimize": "Profile and optimize slow operations",
                "monitor": "Continue monitoring response time trends",
            },
            "error_rate": {
                "scale_up": "Investigate error causes and improve error handling",
                "optimize": "Fix bugs and improve service reliability",
                "monitor": "Monitor error patterns and fix issues proactively",
            },
        }

        metric_actions = actions.get(metric, actions["cpu_usage"])

        # Determine urgency and action based on current state and prediction
        if current_utilization >= 0.95:
            return metric_actions["scale_up"], "critical"
        elif current_utilization >= 0.85:
            return metric_actions["optimize"], "high"
        elif days_until and days_until <= 7:
            return metric_actions["scale_up"], "high"
        elif days_until and days_until <= 30:
            return metric_actions["optimize"], "medium"
        elif current_utilization >= 0.7:
            return metric_actions["monitor"], "medium"
        else:
            return metric_actions["monitor"], "low"


class CapacityPlanner:
    """Main capacity planning orchestrator"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.collector = None
        self.analyzer = TrendAnalyzer()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file"""
        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)

        # Default configuration
        return {
            "prometheus_url": "http://localhost:9090",
            "services": [
                "model-router",
                "plan-management",
                "git-worktree-manager",
                "workflow-orchestrator",
                "verification-feedback",
            ],
            "lookback_days": 7,
            "prediction_horizon_days": 30,
            "thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "response_time_p95": 2.0,
                "error_rate": 0.01,
            },
        }

    async def generate_capacity_report(self) -> Dict:
        """Generate comprehensive capacity planning report"""
        logger.info("Starting capacity planning analysis...")

        async with MetricsCollector(self.config["prometheus_url"]) as collector:
            self.collector = collector

            # Collect resource metrics
            resource_metrics = await collector.get_resource_metrics(
                lookback_days=self.config["lookback_days"]
            )

            # Analyze resource trends
            resource_predictions = self.analyzer.analyze_resource_trends(
                resource_metrics
            )

            # Collect and analyze service metrics
            service_predictions = {}
            for service in self.config["services"]:
                service_metrics = await collector.get_service_metrics(
                    service, lookback_days=self.config["lookback_days"]
                )
                service_preds = self.analyzer.analyze_service_trends(
                    service, service_metrics
                )
                service_predictions.update(service_preds)

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "analysis_period": f"{self.config['lookback_days']} days",
                "prediction_horizon": f"{self.config['prediction_horizon_days']} days",
                "resource_analysis": self._format_predictions(resource_predictions),
                "service_analysis": self._format_predictions(service_predictions),
                "recommendations": self._generate_recommendations(
                    resource_predictions, service_predictions
                ),
                "alerts": self._generate_alerts(
                    resource_predictions, service_predictions
                ),
            }

            return report

    def _format_predictions(
        self, predictions: Dict[str, CapacityPrediction]
    ) -> List[Dict]:
        """Format predictions for report output"""
        formatted = []
        for key, pred in predictions.items():
            formatted.append(
                {
                    "service": pred.service,
                    "metric": pred.metric,
                    "current_value": round(pred.current_value, 2),
                    "predicted_value": round(pred.predicted_value, 2),
                    "confidence_interval": [
                        round(pred.confidence_interval[0], 2),
                        round(pred.confidence_interval[1], 2),
                    ],
                    "days_until_threshold": pred.days_until_threshold,
                    "recommended_action": pred.recommended_action,
                    "urgency": pred.urgency,
                }
            )
        return formatted

    def _generate_recommendations(
        self, resource_preds: Dict, service_preds: Dict
    ) -> List[Dict]:
        """Generate prioritized recommendations"""
        all_predictions = {**resource_preds, **service_preds}

        # Sort by urgency and days until threshold
        urgency_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_preds = sorted(
            all_predictions.items(),
            key=lambda x: (
                urgency_order.get(x[1].urgency, 4),
                x[1].days_until_threshold or 999,
            ),
        )

        recommendations = []
        for key, pred in sorted_preds[:10]:  # Top 10 recommendations
            recommendations.append(
                {
                    "priority": len(recommendations) + 1,
                    "service": pred.service,
                    "metric": pred.metric,
                    "urgency": pred.urgency,
                    "action": pred.recommended_action,
                    "timeline": (
                        f"{pred.days_until_threshold} days"
                        if pred.days_until_threshold
                        else "Monitor"
                    ),
                    "impact": self._assess_impact(pred),
                }
            )

        return recommendations

    def _generate_alerts(self, resource_preds: Dict, service_preds: Dict) -> List[Dict]:
        """Generate capacity-related alerts"""
        all_predictions = {**resource_preds, **service_preds}

        alerts = []
        for key, pred in all_predictions.items():
            if pred.urgency in ["critical", "high"]:
                alerts.append(
                    {
                        "severity": pred.urgency,
                        "service": pred.service,
                        "metric": pred.metric,
                        "message": f"{pred.metric} for {pred.service} requires attention",
                        "current_value": pred.current_value,
                        "days_until_threshold": pred.days_until_threshold,
                        "recommended_action": pred.recommended_action,
                    }
                )

        return alerts

    def _assess_impact(self, prediction: CapacityPrediction) -> str:
        """Assess the impact of reaching the threshold"""
        impact_map = {
            "cpu_usage": "Service degradation, slow response times",
            "memory_usage": "Service crashes, out of memory errors",
            "disk_usage": "Service failures, unable to write data",
            "response_time_p95": "Poor user experience, SLO violations",
            "error_rate": "Service reliability issues, user impact",
        }
        return impact_map.get(prediction.metric, "Service impact possible")


async def main():
    """Main entry point for capacity planning analysis"""
    planner = CapacityPlanner()

    try:
        report = await planner.generate_capacity_report()

        # Output report
        print("\n" + "=" * 60)
        print("EAI-MCP PLATFORM CAPACITY PLANNING REPORT")
        print("=" * 60)
        print(f"Generated: {report['timestamp']}")
        print(f"Analysis Period: {report['analysis_period']}")
        print(f"Prediction Horizon: {report['prediction_horizon']}")

        # Resource Analysis
        print("\n📊 RESOURCE ANALYSIS")
        print("-" * 30)
        for item in report["resource_analysis"]:
            print(
                f"• {item['metric'].upper()}: {item['current_value']}% "
                f"(Predicted: {item['predicted_value']}%) - {item['urgency'].upper()}"
            )

        # Service Analysis
        print("\n🚀 SERVICE ANALYSIS")
        print("-" * 30)
        for item in report["service_analysis"]:
            print(
                f"• {item['service']} {item['metric']}: {item['current_value']} "
                f"(Predicted: {item['predicted_value']}) - {item['urgency'].upper()}"
            )

        # Top Recommendations
        print("\n🎯 TOP RECOMMENDATIONS")
        print("-" * 30)
        for rec in report["recommendations"][:5]:
            print(f"{rec['priority']}. [{rec['urgency'].upper()}] {rec['service']}")
            print(f"   Action: {rec['action']}")
            print(f"   Timeline: {rec['timeline']}")
            print()

        # Alerts
        if report["alerts"]:
            print("\n🚨 CAPACITY ALERTS")
            print("-" * 30)
            for alert in report["alerts"]:
                print(
                    f"[{alert['severity'].upper()}] {alert['service']} - {alert['metric']}"
                )
                print(f"Action: {alert['recommended_action']}")
                print()

        # Save detailed report
        output_file = f"capacity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {output_file}")

    except Exception as e:
        logger.error(f"Error generating capacity report: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
