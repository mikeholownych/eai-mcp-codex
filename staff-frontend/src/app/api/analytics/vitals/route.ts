<<<<<<< HEAD
import { NextRequest, NextResponse } from "next/server";
import { debug, fetchWithTimeout } from "@/lib/utils";
=======
import { NextRequest, NextResponse } from 'next/server'
import { debug, fetchWithTimeout } from '@/lib/utils'
>>>>>>> main

interface WebVital {
  name: string;
  value: number;
  id: string;
  url: string;
  timestamp?: number;
}

export async function POST(request: NextRequest) {
  try {
    const vital: WebVital = await request.json();
<<<<<<< HEAD

    // Add server timestamp
    vital.timestamp = Date.now();

=======
    
    // Add server timestamp
    vital.timestamp = Date.now();
    
>>>>>>> main
    // Log the vital for debugging
    debug(`Web Vital - ${vital.name}`, {
      value: vital.value,
      id: vital.id,
      url: vital.url,
      timestamp: new Date(vital.timestamp).toISOString(),
<<<<<<< HEAD
    });

=======
    })
    
>>>>>>> main
    // In production, you would send this to your analytics service
    // Examples:
    // - Send to Prometheus via pushgateway
    // - Send to custom analytics endpoint
    // - Store in database for analysis
<<<<<<< HEAD

    // Simulate sending to monitoring system
    await sendToMonitoring(vital);

    return NextResponse.json({ success: true });
  } catch (error) {
    debug("Error processing web vital", error);
    return NextResponse.json(
      { error: "Failed to process web vital" },
      { status: 500 },
=======
    
    // Simulate sending to monitoring system
    await sendToMonitoring(vital);
    
    return NextResponse.json({ success: true });
  } catch (error) {
    debug('Error processing web vital', error)
    return NextResponse.json(
      { error: 'Failed to process web vital' },
      { status: 500 }
>>>>>>> main
    );
  }
}

async function sendToMonitoring(vital: WebVital) {
  // Convert Web Vital to Prometheus format
  const prometheusMetric = formatForPrometheus(vital);
<<<<<<< HEAD

=======
  
>>>>>>> main
  try {
    // Send to Prometheus Pushgateway (if available)
    const pushgatewayUrl = process.env.PROMETHEUS_PUSHGATEWAY_URL;
    if (pushgatewayUrl) {
      await fetchWithTimeout(
        `${pushgatewayUrl}/metrics/job/frontend/instance/web-vitals`,
        {
<<<<<<< HEAD
          method: "POST",
          headers: { "Content-Type": "text/plain" },
          body: prometheusMetric,
        },
      );
    }
  } catch (error) {
    debug("Failed to send metrics to Prometheus", error);
=======
          method: 'POST',
          headers: { 'Content-Type': 'text/plain' },
          body: prometheusMetric,
        },
      )
    }
  } catch (error) {
    debug('Failed to send metrics to Prometheus', error)
>>>>>>> main
  }
}

function formatForPrometheus(vital: WebVital): string {
  const metricName = `web_vital_${vital.name.toLowerCase()}`;
  const labels = `{url="${vital.url}",vitals_id="${vital.id}"}`;
<<<<<<< HEAD

=======
  
>>>>>>> main
  return `# HELP ${metricName} Web Vital metric for ${vital.name}
# TYPE ${metricName} gauge
${metricName}${labels} ${vital.value} ${vital.timestamp}
`;
}

// Optional: GET endpoint for health check
export async function GET() {
  return NextResponse.json({
<<<<<<< HEAD
    service: "web-vitals-collector",
    status: "healthy",
    timestamp: new Date().toISOString(),
  });
}
=======
    service: 'web-vitals-collector',
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
}
>>>>>>> main
