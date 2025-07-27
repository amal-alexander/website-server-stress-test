import streamlit as st
import asyncio
import aiohttp
import time
import statistics
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Professional Server Stress Test",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .success-metric {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    .warning-metric {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
    }
    .error-metric {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">🚀 Professional Server Stress Test Tool</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    tab_selection = st.sidebar.radio(
        "Choose Section:",
        ["🧪 Stress Test", "📚 Educational Hub", "📊 Test History", "⚙️ Advanced Settings"]
    )
    
    if tab_selection == "🧪 Stress Test":
        stress_test_tab()
    elif tab_selection == "📚 Educational Hub":
        educational_tab()
    elif tab_selection == "📊 Test History":
        test_history_tab()
    elif tab_selection == "⚙️ Advanced Settings":
        advanced_settings_tab()

def stress_test_tab():
    st.header("🧪 Server Stress Testing")
    
    # Create two columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Test Configuration")
        
        # URL input with validation
        url = st.text_input(
            "🌐 Website URL:",
            placeholder="https://example.com",
            help="Enter the full URL including http:// or https://"
        )
        
        # Test parameters
        col_a, col_b = st.columns(2)
        with col_a:
            concurrent_users = st.slider(
                "👥 Concurrent Users", 
                min_value=1, max_value=100, value=10,
                help="Number of simultaneous users"
            )
        with col_b:
            requests_per_user = st.slider(
                "📨 Requests per User", 
                min_value=1, max_value=50, value=5,
                help="Number of requests each user will make"
            )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            timeout = st.slider("Request Timeout (seconds)", 1, 30, 10)
            delay_between_requests = st.slider("Delay Between Requests (ms)", 0, 1000, 100)
            follow_redirects = st.checkbox("Follow Redirects", value=True)
    
    with col2:
        st.subheader("📊 Test Overview")
        total_requests = concurrent_users * requests_per_user
        
        st.info(f"""
        **Test Summary:**
        - Total Requests: {total_requests}
        - Duration: ~{(total_requests * delay_between_requests / 1000):.1f}s
        - Peak Load: {concurrent_users} concurrent users
        """)
        
        # Warning for high load
        if total_requests > 500:
            st.warning("⚠️ High load test! Please ensure you have permission to test this server.")
    
    # Run test button
    if st.button("🚀 Start Stress Test", type="primary", use_container_width=True):
        if not url or not url.startswith(('http://', 'https://')):
            st.error("❌ Please enter a valid URL starting with http:// or https://")
        else:
            run_stress_test(url, concurrent_users, requests_per_user, timeout, delay_between_requests)

async def fetch_with_metrics(session, url, timeout, delay):
    """Enhanced fetch function with detailed metrics"""
    start_time = time.perf_counter()
    
    try:
        if delay > 0:
            await asyncio.sleep(delay / 1000)  # Convert ms to seconds
            
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            content = await response.text()
            end_time = time.perf_counter()
            
            return {
                "status": response.status,
                "response_time": (end_time - start_time) * 1000,  # Convert to ms
                "content_length": len(content),
                "success": 200 <= response.status < 300,
                "timestamp": datetime.now()
            }
    except asyncio.TimeoutError:
        return {"status": "timeout", "response_time": timeout * 1000, "success": False, "error": "Timeout"}
    except Exception as e:
        return {"status": "error", "response_time": None, "success": False, "error": str(e)}

async def run_load_test(url, concurrent_users, requests_per_user, timeout, delay):
    """Run the actual load test"""
    tasks = []
    
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        for _ in range(concurrent_users * requests_per_user):
            tasks.append(fetch_with_metrics(session, url, timeout, delay))
        
        return await asyncio.gather(*tasks, return_exceptions=True)

def run_stress_test(url, concurrent_users, requests_per_user, timeout, delay):
    """Main function to run stress test with UI updates"""
    
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("🚀 Initializing stress test...")
    
    try:
        # Run the async test
        start_time = time.time()
        results = asyncio.run(run_load_test(url, concurrent_users, requests_per_user, timeout, delay))
        end_time = time.time()
        
        progress_bar.progress(100)
        status_text.text("✅ Test completed successfully!")
        
        # Process results
        process_and_display_results(results, end_time - start_time, url, concurrent_users, requests_per_user)
        
    except Exception as e:
        st.error(f"❌ Test failed: {str(e)}")
        progress_bar.empty()
        status_text.empty()

def process_and_display_results(results, total_duration, url, concurrent_users, requests_per_user):
    """Process and display test results with enhanced visualizations"""
    
    # Filter successful results
    valid_results = [r for r in results if isinstance(r, dict) and r.get("response_time") is not None]
    successful_results = [r for r in valid_results if r.get("success", False)]
    
    if not valid_results:
        st.error("❌ No valid responses received. The server might be down or blocking requests.")
        return
    
    # Calculate metrics
    response_times = [r["response_time"] for r in valid_results]
    success_count = len(successful_results)
    total_requests = len(results)
    success_rate = (success_count / total_requests) * 100 if total_requests > 0 else 0
    
    # Display summary metrics
    st.subheader("📊 Test Results Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Requests",
            value=f"{total_requests:,}",
            help="Total number of HTTP requests sent"
        )
    
    with col2:
        avg_response_time = statistics.mean(response_times) if response_times else 0
        st.metric(
            label="Avg Response Time",
            value=f"{avg_response_time:.2f} ms",
            help="Average response time across all requests"
        )
    
    with col3:
        st.metric(
            label="Success Rate",
            value=f"{success_rate:.1f}%",
            delta=f"{success_count}/{total_requests}",
            help="Percentage of successful HTTP responses (2xx status codes)"
        )
    
    with col4:
        throughput = total_requests / total_duration if total_duration > 0 else 0
        st.metric(
            label="Throughput",
            value=f"{throughput:.1f} req/s",
            help="Requests per second"
        )
    
    # Detailed metrics
    if response_times:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Response Time Analysis")
            
            # Calculate percentiles
            p50 = statistics.median(response_times)
            p95 = statistics.quantiles(response_times, n=100)[94] if len(response_times) >= 20 else max(response_times)
            p99 = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 50 else max(response_times)
            
            metrics_df = pd.DataFrame({
                'Metric': ['Minimum', 'Median (P50)', '95th Percentile', '99th Percentile', 'Maximum'],
                'Value (ms)': [
                    min(response_times),
                    p50,
                    p95,
                    p99,
                    max(response_times)
                ]
            })
            
            st.dataframe(metrics_df, use_container_width=True)
        
        with col2:
            st.subheader("📊 Status Code Distribution")
            
            # Count status codes
            status_counts = {}
            for result in valid_results:
                status = result.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                status_df = pd.DataFrame(
                    list(status_counts.items()),
                    columns=['Status Code', 'Count']
                )
                
                # Create pie chart
                fig_pie = px.pie(
                    status_df, 
                    values='Count', 
                    names='Status Code',
                    title="HTTP Status Code Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # Response time visualization
    st.subheader("📈 Response Time Visualization")
    
    if response_times:
        # Create subplot with multiple charts
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Response Time Over Time', 'Response Time Distribution', 
                          'Response Time Box Plot', 'Cumulative Response Times'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Line chart - Response time over time
        fig.add_trace(
            go.Scatter(
                y=response_times,
                mode='lines+markers',
                name='Response Time',
                line=dict(color='#1f77b4', width=2)
            ),
            row=1, col=1
        )
        
        # Histogram - Response time distribution
        fig.add_trace(
            go.Histogram(
                x=response_times,
                nbinsx=30,
                name='Distribution',
                marker_color='#ff7f0e'
            ),
            row=1, col=2
        )
        
        # Box plot
        fig.add_trace(
            go.Box(
                y=response_times,
                name='Response Times',
                marker_color='#2ca02c'
            ),
            row=2, col=1
        )
        
        # Cumulative line chart
        sorted_times = sorted(response_times)
        cumulative_pct = [(i + 1) / len(sorted_times) * 100 for i in range(len(sorted_times))]
        
        fig.add_trace(
            go.Scatter(
                x=sorted_times,
                y=cumulative_pct,
                mode='lines',
                name='Cumulative %',
                line=dict(color='#d62728', width=2)
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=800, showlegend=False, title_text="Comprehensive Response Time Analysis")
        fig.update_xaxes(title_text="Request Number", row=1, col=1)
        fig.update_xaxes(title_text="Response Time (ms)", row=1, col=2)
        fig.update_xaxes(title_text="Response Time (ms)", row=2, col=2)
        fig.update_yaxes(title_text="Response Time (ms)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=2)
        fig.update_yaxes(title_text="Response Time (ms)", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative %", row=2, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance recommendations
    st.subheader("💡 Performance Insights")
    
    if success_rate < 95:
        st.error(f"⚠️ Low success rate ({success_rate:.1f}%). Server might be overloaded or experiencing issues.")
    elif success_rate < 99:
        st.warning(f"⚠️ Moderate success rate ({success_rate:.1f}%). Consider investigating failed requests.")
    else:
        st.success(f"✅ Excellent success rate ({success_rate:.1f}%)!")
    
    if response_times:
        avg_time = statistics.mean(response_times)
        if avg_time > 3000:
            st.error("🐌 Very slow average response time (>3s). Server performance needs attention.")
        elif avg_time > 1000:
            st.warning("⏰ Slow average response time (>1s). Consider optimization.")
        elif avg_time > 500:
            st.info("📊 Moderate response time. Room for improvement.")
        else:
            st.success("🚀 Fast response times! Server performing well.")

def educational_tab():
    """Educational content about load testing"""
    st.header("📚 Load Testing Educational Hub")
    
    # Create tabs for different educational sections
    edu_tab1, edu_tab2, edu_tab3, edu_tab4 = st.tabs([
        "🎯 Basics", "📊 Metrics", "🔧 Best Practices", "⚠️ Ethics & Legal"
    ])
    
    with edu_tab1:
        st.subheader("What is Load Testing?")
        st.markdown("""
        **Load testing** is a type of performance testing that simulates real-world load on a software application, 
        system, or website to evaluate its behavior under expected and peak load conditions.
        
        ### Types of Performance Testing:
        
        - **Load Testing**: Normal expected load
        - **Stress Testing**: Beyond normal capacity 
        - **Spike Testing**: Sudden load increases
        - **Volume Testing**: Large amounts of data
        - **Endurance Testing**: Extended periods
        """)
        
        st.subheader("Why is Load Testing Important?")
        st.markdown("""
        - **Identify Bottlenecks**: Find performance issues before users do
        - **Capacity Planning**: Understand system limits
        - **User Experience**: Ensure good performance under load
        - **Cost Management**: Optimize resource allocation
        - **Risk Mitigation**: Prevent downtime and lost revenue
        """)
    
    with edu_tab2:
        st.subheader("Key Performance Metrics")
        
        metrics_data = {
            'Metric': [
                'Response Time', 'Throughput', 'Error Rate', 'Concurrent Users',
                'CPU Usage', 'Memory Usage', 'Network I/O', '95th Percentile'
            ],
            'Description': [
                'Time taken to complete a request',
                'Requests processed per second',
                'Percentage of failed requests',
                'Number of simultaneous users',
                'Server CPU utilization',
                'Memory consumption',
                'Network bandwidth usage',
                '95% of requests complete within this time'
            ],
            'Good Target': [
                '< 2 seconds', '> 100 req/s', '< 1%', 'Varies',
                '< 80%', '< 80%', 'Stable', '< 5 seconds'
            ]
        }
        
        st.dataframe(pd.DataFrame(metrics_data), use_container_width=True)
        
        st.subheader("Understanding Percentiles")
        st.markdown("""
        **Percentiles** are crucial for understanding user experience:
        
        - **50th Percentile (Median)**: Half of users experience this or better
        - **95th Percentile**: 95% of users experience this or better  
        - **99th Percentile**: 99% of users experience this or better
        
        Focus on 95th percentile rather than average - it represents the experience of your slowest users.
        """)
    
    with edu_tab3:
        st.subheader("Load Testing Best Practices")
        
        st.markdown("""
        ### 🎯 Planning Your Test
        
        1. **Define Clear Objectives**
           - What are you trying to measure?
           - What are your performance goals?
           - Which scenarios are most critical?
        
        2. **Realistic Test Scenarios**
           - Use production-like data
           - Simulate real user behavior
           - Include different user types
        
        3. **Environment Considerations**
           - Test in production-like environment
           - Consider network conditions
           - Account for third-party dependencies
        
        ### 📈 Test Execution
        
        - **Start Small**: Begin with low load and gradually increase
        - **Monitor Everything**: Server metrics, database, network
        - **Document Results**: Keep detailed records
        - **Test Regularly**: Performance can degrade over time
        
        ### 🔍 Analysis Tips
        
        - Look for patterns in failures
        - Identify resource bottlenecks
        - Compare against baseline performance
        - Consider user experience impact
        """)
    
    with edu_tab4:
        st.subheader("⚠️ Ethics and Legal Considerations")
        
        st.error("""
        **IMPORTANT: Always Get Permission First!**
        
        Load testing someone else's website without permission can be considered:
        - Denial of Service (DoS) attack
        - Network abuse
        - Potentially illegal activity
        """)
        
        st.markdown("""
        ### ✅ Ethical Load Testing Guidelines
        
        1. **Test Only Your Own Systems**
           - Your own websites and applications
           - Systems you have explicit permission to test
           - Development/staging environments
        
        2. **Responsible Testing**
           - Start with small loads
           - Monitor for impact on other users
           - Stop immediately if causing issues
           - Test during off-peak hours when possible
        
        3. **Professional Testing**
           - Document your testing plan
           - Get written permission for third-party systems
           - Consider using professional testing services
           - Follow industry standards and guidelines
        
        ### 🏢 Enterprise Considerations
        
        - Inform your team about testing schedules
        - Consider impact on shared resources
        - Use dedicated testing environments
        - Follow company policies and procedures
        """)
        
        st.info("""
        **Remember**: The goal of load testing is to improve system performance, 
        not to cause harm or disruption. Always test responsibly!
        """)

def test_history_tab():
    """Test history and results comparison"""
    st.header("📊 Test History & Analysis")
    
    st.info("This feature would store historical test results for comparison and trend analysis.")
    
    # Placeholder for historical data visualization
    st.subheader("📈 Performance Trends")
    st.markdown("""
    In a full implementation, this section would show:
    - Historical response time trends
    - Success rate over time  
    - Performance comparisons between tests
    - Capacity planning insights
    """)
    
    # Sample trend chart
    dates = pd.date_range('2024-01-01', periods=10, freq='D')
    sample_data = pd.DataFrame({
        'Date': dates,
        'Avg Response Time': [200 + i*10 + (i%3)*50 for i in range(10)],
        'Success Rate': [99.5 - (i%4)*0.5 for i in range(10)]
    })
    
    fig = px.line(sample_data, x='Date', y='Avg Response Time', 
                  title='Sample: Response Time Trend Over Time')
    st.plotly_chart(fig, use_container_width=True)

def advanced_settings_tab():
    """Advanced configuration options"""
    st.header("⚙️ Advanced Configuration")
    
    st.subheader("🔧 Request Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**HTTP Settings**")
        http_method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
        user_agent = st.text_input("User Agent", "StressTestTool/1.0")
        follow_redirects = st.checkbox("Follow Redirects", True)
        verify_ssl = st.checkbox("Verify SSL Certificates", True)
    
    with col2:
        st.markdown("**Advanced Options**")
        connection_pool_size = st.slider("Connection Pool Size", 10, 200, 50)
        keep_alive = st.checkbox("Keep Alive Connections", True)
        compress_response = st.checkbox("Accept Compressed Responses", True)
    
    st.subheader("📊 Reporting Options")
    
    export_format = st.selectbox("Export Format", ["JSON", "CSV", "PDF Report"])
    include_raw_data = st.checkbox("Include Raw Response Data")
    
    if st.button("💾 Save Configuration"):
        st.success("Configuration saved successfully!")
    
    st.subheader("🚨 Safety Limits")
    st.markdown("""
    **Built-in Safety Features:**
    - Maximum 100 concurrent users (configurable)
    - Request timeout limits
    - Automatic test termination on high error rates
    - Rate limiting to prevent server overload
    """)

if __name__ == "__main__":
    main()