import React, { useState } from "react";
import { Layout, Form, Input, DatePicker, Button, Card, message, Spin, Tabs, Tag, Timeline, Typography, Divider, Space } from "antd";
import type { FormProps } from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";

const { Header, Content } = Layout;
const { Title, Text, Paragraph } = Typography;

const API_BASE_URL = "http://localhost:8000";

interface ExecutionStep {
  step?: number;
  type?: string;
  tool_calls?: Array<{ name?: string; args?: any }>;
  content_preview?: string;
  content?: string;
}

interface AgentLog {
  agent: string;
  status: string;
  execution_steps?: ExecutionStep[];
  tool_calls_count?: number;
}

interface PlanResult {
  trip_config?: any;
  itinerary?: any;
  hotels?: any;
  flights?: any;
  execution_log?: AgentLog[];
}

const App: React.FC = () => {
  const [result, setResult] = useState<PlanResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [form] = Form.useForm();

  const handleSubmit: FormProps["onFinish"] = async (values: any) => {
    try {
      setLoading(true);
      setResult(null);

      // Convert dayjs objects to YYYY-MM-DD format
      const departureDate = values.departure_date as Dayjs;
      const returnDate = values.return_date as Dayjs;

      if (!departureDate || !returnDate) {
        message.error("Please select both departure and return dates");
        setLoading(false);
        return;
      }

      // Prepare request data with date format conversion
      const requestData = {
        origin_city: values.origin_city,
        destination_city: values.destination_city,
        departure_date: departureDate.format("YYYY-MM-DD"),
        return_date: returnDate.format("YYYY-MM-DD"),
        num_people: parseInt(values.num_people),
        budget: parseFloat(values.budget),
      };

      // Call backend API with verbose mode
      const response = await fetch(`${API_BASE_URL}/api/plan/verbose`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const resultData = await response.json();
      setResult(resultData);
      message.success("Travel plan generated successfully!");
    } catch (error: any) {
      console.error("Error generating plan:", error);
      message.error(error.message || "Failed to generate travel plan");
    } finally {
      setLoading(false);
    }
  };

  // Helper function to generate attraction description
  const getAttractionDescription = (attraction: any): string => {
    // If description is already provided, use it
    if (attraction.description) {
      return attraction.description;
    }
    
    const name = attraction.name?.toLowerCase() || "";
    
    // Generate description based on attraction name patterns
    if (name.includes("museum")) {
      return "Explore fascinating exhibits, art collections, and cultural artifacts. Perfect for learning about history, art, and science.";
    } else if (name.includes("park") || name.includes("garden")) {
      return "Enjoy beautiful landscapes, walking trails, and outdoor activities. Great for relaxation and nature appreciation.";
    } else if (name.includes("square") || name.includes("plaza")) {
      return "Experience the vibrant city atmosphere, street performances, shopping, and local culture.";
    } else if (name.includes("bridge")) {
      return "Walk across this iconic landmark, enjoy scenic views, and capture stunning photos.";
    } else if (name.includes("tower") || name.includes("building")) {
      return "Visit this architectural marvel, enjoy panoramic city views, and learn about its history.";
    } else if (name.includes("memorial") || name.includes("monument")) {
      return "Pay tribute to historical events and figures. A meaningful place for reflection and learning.";
    } else if (name.includes("beach") || name.includes("coast")) {
      return "Relax on the sandy shores, enjoy water activities, and soak up the sun.";
    } else if (name.includes("zoo") || name.includes("aquarium")) {
      return "Discover diverse wildlife, learn about animals, and enjoy family-friendly entertainment.";
    } else if (name.includes("cathedral") || name.includes("church") || name.includes("temple")) {
      return "Admire stunning architecture, learn about religious history, and experience peaceful surroundings.";
    } else if (name.includes("market") || name.includes("bazaar")) {
      return "Browse local products, try authentic food, and experience the local shopping culture.";
    } else {
      return "Explore this popular attraction, discover its unique features, and create memorable experiences.";
    }
  };

  // Helper function to render execution summary
  const renderExecutionSummary = (executionLog: AgentLog[]) => {
    if (!executionLog || executionLog.length === 0) return null;

    const agentNames: { [key: string]: string } = {
      planner_agent: "Planner Agent",
      hotel_agent: "Hotel Agent",
      flight_agent: "Flight Agent",
    };

    return (
      <Card
        title={<Title level={4} style={{ margin: 0 }}>Execution Summary</Title>}
        style={{ marginBottom: 24 }}
      >
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          {executionLog.map((log, index) => (
            <div key={index} style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <Tag color={log.status === "completed" ? "green" : "orange"}>
                {log.status.toUpperCase()}
              </Tag>
              <Text strong>{agentNames[log.agent] || log.agent}</Text>
              <Text type="secondary">
                Tool calls: {log.tool_calls_count || 0}
              </Text>
            </div>
          ))}
        </Space>
      </Card>
    );
  };

  // Helper function to render execution details
  const renderExecutionDetails = (executionLog: AgentLog[]) => {
    if (!executionLog || executionLog.length === 0) return null;

    const agentNames: { [key: string]: string } = {
      planner_agent: "Planner Agent",
      hotel_agent: "Hotel Agent",
      flight_agent: "Flight Agent",
    };

  return (
      <Card
        title={<Title level={4} style={{ margin: 0 }}>Execution Process Details</Title>}
        style={{ marginBottom: 24 }}
      >
        {executionLog.map((log, agentIndex) => (
          <div key={agentIndex} style={{ marginBottom: 32 }}>
            <Title level={5} style={{ marginBottom: 16 }}>
              {agentNames[log.agent] || log.agent.toUpperCase()}
            </Title>
            <Divider />
            <div style={{ marginBottom: 16 }}>
              <Text type="secondary">
                Total execution steps: {log.execution_steps?.length || 0}
              </Text>
              <br />
              <Text type="secondary">
                Tool calls: {log.tool_calls_count || 0}
              </Text>
            </div>
            {log.execution_steps && log.execution_steps.length > 0 && (
              <Timeline>
                {log.execution_steps.map((step, stepIndex) => (
                  <Timeline.Item key={stepIndex}>
                    <div>
                      <Text strong>
                        Step {step.step || stepIndex + 1} [{step.type || "unknown"}]
                      </Text>
                      {step.tool_calls && step.tool_calls.length > 0 && (
                        <div style={{ marginTop: 8, marginLeft: 16 }}>
                          {step.tool_calls.map((toolCall, toolIndex) => (
                            <div key={toolIndex} style={{ marginBottom: 8 }}>
                              <Tag color="blue">Tool: {toolCall.name || "unknown"}</Tag>
                              {toolCall.args && (
                                <div style={{ marginTop: 4, marginLeft: 8 }}>
                                  <Text type="secondary" style={{ fontSize: 12 }}>
                                    {JSON.stringify(toolCall.args, null, 2).substring(0, 200)}
                                    {JSON.stringify(toolCall.args).length > 200 ? "..." : ""}
                                  </Text>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      {(step.content_preview || step.content) && (
                        <div style={{ marginTop: 8, marginLeft: 16 }}>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {step.content_preview || 
                             (step.content && step.content.length > 150 
                               ? step.content.substring(0, 150) + "..." 
                               : step.content)}
                          </Text>
                        </div>
                      )}
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            )}
          </div>
        ))}
      </Card>
    );
  };

  // Helper function to render final results
  const renderFinalResults = (result: PlanResult) => {
    const tabItems = [
      {
        key: "itinerary",
        label: "Itinerary",
        children: (
          <div>
            {result.itinerary && (
              <div>
                <Title level={5}>Destination: {result.itinerary.destination}</Title>
                {result.itinerary.days && result.itinerary.days.map((day: any, index: number) => (
                  <Card key={index} style={{ marginBottom: 16 }}>
                    <Title level={5}>{day.date || `Day ${day.day_index}`}</Title>
                    <Space direction="vertical" size="small" style={{ width: "100%" }}>
                      {day.morning && day.morning.length > 0 && (
                        <div>
                          <Text strong>Morning:</Text>
                          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                            {day.morning.map((attraction: any, i: number) => (
                              <li key={i} style={{ marginBottom: 12 }}>
                                <div>
                                  <Text strong style={{ fontSize: 15 }}>{attraction.name}</Text>
                                </div>
                                <div style={{ marginTop: 4 }}>
                                  <Text type="secondary" style={{ fontSize: 13, fontStyle: "italic" }}>
                                    {getAttractionDescription(attraction)}
                                  </Text>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {day.afternoon && day.afternoon.length > 0 && (
                        <div>
                          <Text strong>Afternoon:</Text>
                          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                            {day.afternoon.map((attraction: any, i: number) => (
                              <li key={i} style={{ marginBottom: 12 }}>
                                <div>
                                  <Text strong style={{ fontSize: 15 }}>{attraction.name}</Text>
                                </div>
                                <div style={{ marginTop: 4 }}>
                                  <Text type="secondary" style={{ fontSize: 13, fontStyle: "italic" }}>
                                    {getAttractionDescription(attraction)}
                                  </Text>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {day.evening && day.evening.length > 0 && (
                        <div>
                          <Text strong>Evening:</Text>
                          <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                            {day.evening.map((attraction: any, i: number) => (
                              <li key={i} style={{ marginBottom: 12 }}>
                                <div>
                                  <Text strong style={{ fontSize: 15 }}>{attraction.name}</Text>
                                </div>
                                <div style={{ marginTop: 4 }}>
                                  <Text type="secondary" style={{ fontSize: 13, fontStyle: "italic" }}>
                                    {getAttractionDescription(attraction)}
                                  </Text>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </Space>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ),
      },
      {
        key: "hotels",
        label: "Hotels",
        children: (
          <div>
            {result.hotels && (
              <div>
                <Paragraph>
                  <Text strong>Destination:</Text> {result.hotels.destination}
                  <br />
                  <Text strong>Nights:</Text> {result.hotels.nights}
                  <br />
                  <Text strong>Hotel Budget per Night:</Text> ${result.hotels.hotel_budget_per_night}
                </Paragraph>
                {result.hotels.recommended_hotels && result.hotels.recommended_hotels.map((hotel: any, index: number) => (
                  <Card key={index} style={{ marginBottom: 16 }}>
                    <Title level={5}>{hotel.name}</Title>
                    <Space direction="vertical" size="small">
                      <div>
                        <Text strong>Price per Night: </Text>
                        <Text style={{ color: "#1890ff", fontSize: 18, fontWeight: 600 }}>
                          ${hotel.price_per_night}
                        </Text>
                      </div>
                      <div>
                        <Text strong>Total Price: </Text>
                        <Text style={{ color: "#52c41a", fontSize: 16, fontWeight: 600 }}>
                          ${hotel.total_price}
                        </Text>
                      </div>
                      <div>
                        <Text strong>Rating: </Text>
                        <Tag color="gold">{hotel.rating} / 5</Tag>
                      </div>
                      {hotel.reason && (
                        <div>
                          <Text strong>Reason: </Text>
                          <Text>{hotel.reason}</Text>
                        </div>
                      )}
                    </Space>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ),
      },
      {
        key: "flights",
        label: "Flights",
        children: (
          <div>
            {result.flights && (
              <div>
                {result.flights.outbound && (
                  <Card style={{ marginBottom: 16 }}>
                    <Title level={5}>Outbound Flights</Title>
                    <Text type="secondary">Destination: {result.flights.outbound.destination}</Text>
                    {result.flights.outbound.recommended_flights && 
                     result.flights.outbound.recommended_flights.map((flight: any, index: number) => (
                      <Card key={index} size="small" style={{ marginTop: 12 }}>
                        <Space direction="vertical" size="small">
                          <div>
                            <Text strong>Airline: </Text>
                            <Tag color="blue">{flight.airline}</Tag>
                          </div>
                          <div>
                            <Text strong>Price: </Text>
                            <Text style={{ color: "#1890ff", fontSize: 16, fontWeight: 600 }}>
                              ${flight.price}
                            </Text>
                            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                              (for all travelers, one-way)
                            </Text>
                          </div>
                          <div>
                            <Text strong>Departure: </Text>
                            <Text>{flight.departure_time}</Text>
                          </div>
                          <div>
                            <Text strong>Arrival: </Text>
                            <Text>{flight.arrival_time}</Text>
                          </div>
                        </Space>
                      </Card>
                    ))}
                  </Card>
                )}
                {result.flights.return && (
                  <Card>
                    <Title level={5}>Return Flights</Title>
                    <Text type="secondary">Destination: {result.flights.return.destination}</Text>
                    {result.flights.return.recommended_flights && 
                     result.flights.return.recommended_flights.map((flight: any, index: number) => (
                      <Card key={index} size="small" style={{ marginTop: 12 }}>
                        <Space direction="vertical" size="small">
                          <div>
                            <Text strong>Airline: </Text>
                            <Tag color="blue">{flight.airline}</Tag>
                          </div>
                          <div>
                            <Text strong>Price: </Text>
                            <Text style={{ color: "#1890ff", fontSize: 16, fontWeight: 600 }}>
                              ${flight.price}
                            </Text>
                            <Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                              (for all travelers, one-way)
                            </Text>
                          </div>
                          <div>
                            <Text strong>Departure: </Text>
                            <Text>{flight.departure_time}</Text>
                          </div>
                          <div>
                            <Text strong>Arrival: </Text>
                            <Text>{flight.arrival_time}</Text>
                          </div>
                        </Space>
                      </Card>
                    ))}
                  </Card>
                )}
              </div>
            )}
          </div>
        ),
      },
      {
        key: "budget",
        label: "Budget",
        children: (
          <div>
            {result.trip_config && (
              <Card>
                <Title level={5}>Budget Summary</Title>
                <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                  <div>
                    <Text strong>Total Budget: </Text>
                    <Text style={{ color: "#1890ff", fontSize: 20, fontWeight: 700 }}>
                      ${result.trip_config.total_budget}
                    </Text>
                  </div>
                  {result.flights && result.flights.outbound && result.flights.return && (
                    <div>
                      <Text strong>Estimated Flight Cost: </Text>
                      <Text style={{ color: "#52c41a", fontSize: 16 }}>
                        ${((result.flights.outbound.recommended_flights?.[0]?.price || 0) + 
                          (result.flights.return.recommended_flights?.[0]?.price || 0)).toFixed(2)}
                      </Text>
                    </div>
                  )}
                  {result.hotels && result.hotels.recommended_hotels && (
                    <div>
                      <Text strong>Estimated Hotel Cost: </Text>
                      <Text style={{ color: "#52c41a", fontSize: 16 }}>
                        ${result.hotels.recommended_hotels[0]?.total_price || 0}
                      </Text>
                    </div>
                  )}
                </Space>
              </Card>
            )}
          </div>
        ),
      },
    ];

    return <Tabs items={tabItems} />;
  };

  return (
    <Layout style={{ minHeight: "100vh", background: "#f5f5f5" }}>
      {/* Header */}
      <Header
        style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          padding: "20px 20px",
          borderBottom: "none",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <h1
          style={{
            fontSize: "36px",
            fontWeight: 700,
            color: "#fff",
            margin: 0,
            textAlign: "center",
            textShadow: "3px 3px 6px rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 255, 255, 0.3)",
            letterSpacing: "3px",
            fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
          }}
        >
          Travel Planner System
        </h1>
      </Header>

      {/* Content */}
      <Content style={{ padding: "40px 80px" }}>
        {/* Top Form (horizontal layout) */}
        <Card
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: 20,
            borderRadius: 10,
          }}
        >
        {/* Instruction Text */}
        <div
          style={{
            marginBottom: 24,
            padding: "16px 20px",
            background: "linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%)",
            borderRadius: 8,
            borderLeft: "4px solid #667eea",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: "15px",
              color: "#424242",
              lineHeight: "1.6",
              fontWeight: 500,
            }}
          >
             <strong>Please provide the following information to generate your personalized travel plan:</strong>
          </p>
          <ul
            style={{
              margin: "12px 0 0 0",
              paddingLeft: 24,
              color: "#616161",
              fontSize: "14px",
              lineHeight: "1.8",
            }}
          >
            <li>Origin and destination cities</li>
            <li>Travel dates (departure and return)</li>
            <li>Number of travelers</li>
            <li>Total budget in USD</li>
          </ul>
        </div>

        <Form
          form={form}
          onFinish={handleSubmit}
          layout="vertical"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          {/* ---------- 第一行：城市 ---------- */}
          <div style={{ display: "flex", gap: 20 }}>
            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600 }}>Origin City</span>}
              name="origin_city"
              rules={[{ required: true, message: "Required" }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="e.g., Seattle" />
            </Form.Item>

            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600 }}>Destination City</span>}
              name="destination_city"
              rules={[{ required: true, message: "Required" }]}
              style={{ flex: 1 }}
            >
              <Input placeholder="e.g., New York" />
            </Form.Item>
          </div>

          {/* ---------- 第二行：日期 + 人数 + 预算 ---------- */}
          <div
            style={{
              display: "flex",
              gap: 20,
              alignItems: "flex-end",
              flexWrap: "wrap",
            }}
          >
            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600 }}>Departure Date</span>}
              name="departure_date"
              rules={[{ required: true, message: "Required" }]}
              style={{ width: 200 }}
            >
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>

            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600 }}>Return Date</span>}
              name="return_date"
              rules={[{ required: true, message: "Required" }]}
              style={{ width: 200 }}
            >
              <DatePicker style={{ width: "100%" }} />
            </Form.Item>

            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600, whiteSpace: "nowrap" }}>Number of Travelers</span>}
              name="num_people"
              rules={[{ required: true, message: "Required" }]}
              style={{ width: 180 }}
            >
              <Input type="number" min={1} />
            </Form.Item>

            <Form.Item
              label={<span style={{ fontSize: "16px", fontWeight: 600 }}>Budget (USD)</span>}
              name="budget"
              rules={[{ required: true, message: "Required" }]}
              style={{ width: 160 }}
            >
              <Input type="number" min={1} />
            </Form.Item>
          </div>

          {/* ---------- 最底部按钮（居中） ---------- */}
          <div style={{ textAlign: "center", marginTop: 10 }}>
          <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              style={{
                padding: "0 40px",
                height: 40,
                fontSize: 16,
                fontWeight: 600,
              }}
            >
              Generate Plan
            </Button>
          </div>
        </Form>
        </Card>

      {/* Results Display Box */}
      {loading ? (
        <Card
          style={{
            maxWidth: 1200,
            margin: "30px auto",
            padding: "24px",
            borderRadius: 12,
            minHeight: "60vh",
            background: "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
            border: "2px solid #667eea",
            boxShadow: "0 4px 20px rgba(102, 126, 234, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 40,
            }}
          >
            <Spin size="large" />
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 20,
              }}
            >
              <span
                style={{
                  fontSize: "18px",
                  fontWeight: 600,
                  color: "#1890ff",
                  letterSpacing: "1px",
                }}
              >
                Generating your travel plan... Please wait...
              </span>
              <p
                style={{
                  margin: 0,
                  fontSize: "16px",
                  color: "#666",
                }}
              >
                Our AI agents are working hard to create the perfect itinerary for you!
              </p>
            </div>
          </div>
        </Card>
      ) : result ? (
        <div style={{ maxWidth: 1200, margin: "30px auto" }}>
          {/* Execution Summary */}
          {result.execution_log && renderExecutionSummary(result.execution_log)}
          
          {/* Execution Details */}
          {result.execution_log && renderExecutionDetails(result.execution_log)}
          
          {/* Final Results */}
          <Card
            title={<Title level={4} style={{ margin: 0 }}>Travel Plan Results</Title>}
            style={{ marginBottom: 24 }}
          >
            {renderFinalResults(result)}
          </Card>
        </div>
      ) : (
        <Card
          style={{
            maxWidth: 1200,
            margin: "30px auto",
            padding: "24px",
            borderRadius: 12,
            minHeight: "60vh",
            background: "#fafafa",
            border: "1.5px solid #d0d0d0",
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span style={{ color: "#999", fontSize: 16 }}>
            Your trip will appear here...
          </span>
        </Card>
      )}
        </Content>
    </Layout>
  );
};

export default App;
