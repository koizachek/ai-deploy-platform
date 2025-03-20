import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { ArrowUpRight, ArrowDownRight, DollarSign, Clock, Server, Cpu, Memory, AlertTriangle } from 'lucide-react';

export default function Dashboard() {
  const [costData, setCostData] = useState(null);
  const [performanceData, setPerformanceData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [suggestionsData, setSuggestionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // In a real implementation, these would be actual API calls
        // For this implementation, we'll use mock data
        
        // Fetch cost analysis
        const costResponse = await mockFetchCostAnalysis();
        setCostData(costResponse);
        
        // Fetch performance analysis
        const performanceResponse = await mockFetchPerformanceAnalysis();
        setPerformanceData(performanceResponse);
        
        // Fetch usage forecast
        const forecastResponse = await mockFetchUsageForecast();
        setForecastData(forecastResponse);
        
        // Fetch optimization suggestions
        const suggestionsResponse = await mockFetchOptimizationSuggestions();
        setSuggestionsData(suggestionsResponse);
        
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Mock API functions
  const mockFetchCostAnalysis = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return {
      timestamp: "2025-03-20T18:00:00Z",
      total_cost: 125.75,
      cost_breakdown: {
        compute: 85.25,
        storage: 25.50,
        network: 15.00
      },
      cost_by_type: {
        kubernetes: 75.50,
        serverless: 50.25
      },
      cost_by_deployment: {
        "llm-inference": 45.25,
        "image-generation": 35.75,
        "text-classification": 25.50,
        "object-detection": 15.25,
        "sentiment-analysis": 4.00
      },
      comparison: {
        our_platform: 125.75,
        aws: 180.25,
        azure: 175.50,
        gcp: 165.75,
        savings_percentage: {
          aws: 30.25,
          azure: 28.35,
          gcp: 24.15
        }
      },
      recommendations: [
        {
          type: "high_cost_deployments",
          message: "Consider optimizing high-cost deployments: llm-inference, image-generation",
          impact: "high"
        },
        {
          type: "serverless_migration",
          message: "Consider migrating low-traffic deployments to serverless for cost savings",
          impact: "medium"
        },
        {
          type: "spot_instances",
          message: "Use spot/preemptible instances for non-critical workloads to reduce costs",
          impact: "high"
        }
      ]
    };
  };
  
  const mockFetchPerformanceAnalysis = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 700));
    
    return {
      timestamp: "2025-03-20T18:00:00Z",
      total_requests: 125000,
      avg_latency: 85.5,
      error_rate: 0.75,
      performance_by_type: {
        kubernetes: {
          requests: 75000,
          avg_latency: 95.25,
          error_rate: 0.85
        },
        serverless: {
          requests: 50000,
          avg_latency: 70.50,
          error_rate: 0.60
        }
      },
      performance_by_deployment: {
        "llm-inference": {
          requests: 45000,
          avg_latency: 120.75,
          error_rate: 0.95
        },
        "image-generation": {
          requests: 35000,
          avg_latency: 105.50,
          error_rate: 0.80
        },
        "text-classification": {
          requests: 25000,
          avg_latency: 65.25,
          error_rate: 0.50
        },
        "object-detection": {
          requests: 15000,
          avg_latency: 85.75,
          error_rate: 0.65
        },
        "sentiment-analysis": {
          requests: 5000,
          avg_latency: 45.25,
          error_rate: 0.35
        }
      },
      recommendations: [
        {
          type: "high_latency_deployments",
          message: "Consider optimizing high-latency deployments: llm-inference, image-generation",
          impact: "high"
        },
        {
          type: "model_optimization",
          message: "Consider optimizing models using quantization, pruning, or distillation to improve performance",
          impact: "medium"
        },
        {
          type: "caching",
          message: "Implement caching for frequent requests to reduce latency and costs",
          impact: "medium"
        }
      ],
      anomalies: {
        "deployment-123": [
          {
            type: "high_error_rate",
            message: "High error rate detected: 5.5% (threshold: 5%)",
            timestamp: "2025-03-20T17:45:00Z"
          },
          {
            type: "high_latency",
            message: "High latency detected: 1250ms (threshold: 1000ms)",
            timestamp: "2025-03-20T17:30:00Z"
          }
        ]
      }
    };
  };
  
  const mockFetchUsageForecast = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 600));
    
    // Generate forecast data for 30 days
    const total_requests_forecast = Array.from({ length: 30 }, (_, i) => 
      Math.round(125000 * (1 + 0.05) ** (i + 1))
    );
    
    const total_cost_forecast = Array.from({ length: 30 }, (_, i) => 
      125.75 * (1 + 0.05) ** (i + 1)
    );
    
    return {
      timestamp: "2025-03-20T18:00:00Z",
      days: 30,
      total_requests_forecast,
      total_cost_forecast,
      forecast_by_deployment: {
        "llm-inference": {
          deployment_name: "llm-inference",
          current_requests: 45000,
          current_cost: 45.25,
          requests_forecast: Array.from({ length: 30 }, (_, i) => 
            Math.round(45000 * (1 + 0.05) ** (i + 1))
          ),
          cost_forecast: Array.from({ length: 30 }, (_, i) => 
            45.25 * (1 + 0.05) ** (i + 1)
          )
        },
        "image-generation": {
          deployment_name: "image-generation",
          current_requests: 35000,
          current_cost: 35.75,
          requests_forecast: Array.from({ length: 30 }, (_, i) => 
            Math.round(35000 * (1 + 0.05) ** (i + 1))
          ),
          cost_forecast: Array.from({ length: 30 }, (_, i) => 
            35.75 * (1 + 0.05) ** (i + 1)
          )
        },
        "text-classification": {
          deployment_name: "text-classification",
          current_requests: 25000,
          current_cost: 25.50,
          requests_forecast: Array.from({ length: 30 }, (_, i) => 
            Math.round(25000 * (1 + 0.05) ** (i + 1))
          ),
          cost_forecast: Array.from({ length: 30 }, (_, i) => 
            25.50 * (1 + 0.05) ** (i + 1)
          )
        },
        "object-detection": {
          deployment_name: "object-detection",
          current_requests: 15000,
          current_cost: 15.25,
          requests_forecast: Array.from({ length: 30 }, (_, i) => 
            Math.round(15000 * (1 + 0.05) ** (i + 1))
          ),
          cost_forecast: Array.from({ length: 30 }, (_, i) => 
            15.25 * (1 + 0.05) ** (i + 1)
          )
        },
        "sentiment-analysis": {
          deployment_name: "sentiment-analysis",
          current_requests: 5000,
          current_cost: 4.00,
          requests_forecast: Array.from({ length: 30 }, (_, i) => 
            Math.round(5000 * (1 + 0.05) ** (i + 1))
          ),
          cost_forecast: Array.from({ length: 30 }, (_, i) => 
            4.00 * (1 + 0.05) ** (i + 1)
          )
        }
      }
    };
  };
  
  const mockFetchOptimizationSuggestions = async () => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));
    
    return {
      timestamp: "2025-03-20T18:00:00Z",
      suggestions_by_deployment: {
        "deployment-123": {
          deployment_name: "llm-inference",
          suggestions: [
            {
              type: "cpu_over_provisioned",
              message: "CPU is over-provisioned. Average utilization: 25.50%",
              current_value: "4",
              recommended_value: "2",
              impact: "medium"
            },
            {
              type: "enable_spot_instances",
              message: "Enable spot/preemptible instances to reduce costs",
              impact: "high"
            },
            {
              type: "high_latency",
              message: "High latency detected. Consider optimizing the model or increasing resources",
              impact: "high"
            }
          ]
        },
        "deployment-456": {
          deployment_name: "image-generation",
          suggestions: [
            {
              type: "memory_over_provisioned",
              message: "Memory is over-provisioned. Average utilization: 28.75%",
              current_value: "8Gi",
              recommended_value: "4Gi",
              impact: "medium"
            },
            {
              type: "enable_hibernation",
              message: "Enable hibernation for inactive deployments to reduce costs",
              impact: "high"
            }
          ]
        },
        "deployment-789": {
          deployment_name: "text-classification",
          suggestions: [
            {
              type: "migrate_to_serverless",
              message: "Consider migrating to serverless deployment for low-traffic workload",
              impact: "high"
            }
          ]
        }
      }
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-lg">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto" />
          <p className="mt-4 text-lg">Error loading dashboard: {error}</p>
          <Button className="mt-4" onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const costBreakdownData = Object.entries(costData.cost_breakdown).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }));

  const costByTypeData = Object.entries(costData.cost_by_type).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }));

  const costByDeploymentData = Object.entries(costData.cost_by_deployment)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  const costComparisonData = [
    { name: 'Our Platform', value: costData.comparison.our_platform },
    { name: 'AWS', value: costData.comparison.aws },
    { name: 'Azure', value: costData.comparison.azure },
    { name: 'GCP', value: costData.comparison.gcp }
  ];

  const forecastChartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    requests: forecastData.total_requests_forecast[i],
    cost: forecastData.total_cost_forecast[i]
  }));

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">AI Deploy Platform Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <DollarSign className="h-4 w-4 text-muted-foreground mr-2" />
              <div className="text-2xl font-bold">${costData.total_cost.toFixed(2)}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              <span className="text-green-500 flex items-center">
                <ArrowDownRight className="h-4 w-4 mr-1" />
                {costData.comparison.savings_percentage.aws.toFixed(1)}% vs AWS
              </span>
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Server className="h-4 w-4 text-muted-foreground mr-2" />
              <div className="text-2xl font-bold">{performanceData.total_requests.toLocaleString()}</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across {Object.keys(performanceData.performance_by_deployment).length} deployments
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg. Latency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <Clock className="h-4 w-4 text-muted-foreground mr-2" />
              <div className="text-2xl font-bold">{performanceData.avg_latency.toFixed(1)} ms</div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Error rate: {performanceData.error_rate.toFixed(2)}%
            </p>
          </CardContent>
        </Card>
      </div>
      
      <Tabs defaultValue="cost" className="mb-8">
        <TabsList className="mb-4">
          <TabsTrigger value="cost">Cost Analysis</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="forecast">Forecast</TabsTrigger>
          <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="cost">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Cost Breakdown</CardTitle>
                <CardDescription>Cost distribution by category</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={costBreakdownData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                      <Legend />
                      <Bar dataKey="value" name="Cost" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>Cost by Deployment Type</CardTitle>
                <CardDescription>Kubernetes vs Serverless</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveCon<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>