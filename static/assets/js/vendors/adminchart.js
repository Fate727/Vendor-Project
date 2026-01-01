// adminchart.js - Shows seller name: amount they sold
const theme = {
    primary: "var(--fc-primary)",
    secondary: "var(--fc-secondary)",
    success: "var(--fc-success)",
    info: "var(--fc-info)",
    warning: "var(--fc-warning)",
    danger: "var(--fc-danger)",
    dark: "var(--fc-dark)",
    light: "var(--fc-light)",
    white: "var(--fc-white)",
    gray100: "var(--fc-gray-100)",
    gray200: "var(--fc-gray-200)",
    gray300: "var(--fc-gray-300)",
    gray400: "var(--fc-gray-400)",
    gray500: "var(--fc-gray-500)",
    gray600: "var(--fc-gray-600)",
    gray700: "var(--fc-gray-700)",
    gray800: "var(--fc-gray-800)",
    gray900: "var(--fc-gray-900)",
    black: "var(--fc-black)",
    transparent: "transparent"
};

window.theme = theme;

(function() {
    "use strict";
    
    // Get chart data for admin dashboard
    function getAdminChartData() {
        try {
            const dataElement = document.getElementById('chartData');
            if (!dataElement) {
                console.log("No chartData element found");
                return null;
            }
            
            const jsonText = dataElement.textContent.trim();
            if (!jsonText) {
                console.log("chartData is empty");
                return null;
            }
            
            const data = JSON.parse(jsonText);
            return data;
            
        } catch (error) {
            console.error("Error getting chart data:", error);
            return null;
        }
    }
    
    // Sellers Performance Chart (Line Chart - Top Sellers)
    if (document.getElementById("sellersChart")) {
        try {
            console.log("=== Initializing sellers chart ===");
            
            // Get chart data
            const chartData = getAdminChartData();
            let dates = [];
            let seriesData = [];
            
            if (chartData && chartData.dates) {
                dates = chartData.dates;
                
                // If we have multiple sellers in series
                if (chartData.series && Array.isArray(chartData.series)) {
                    seriesData = chartData.series;
                } else {
                    // Fallback to single series
                    seriesData = [{
                        name: "Platform Sales",
                        data: chartData.daily_totals || [0, 0, 0, 0, 0, 0, 0],
                        color: "#4e73df"
                    }];
                }
            } else {
                // Generate example labels for last 7 days
                const today = new Date();
                dates = [];
                for (let i = 0; i < 7; i++) {
                    const date = new Date(today);
                    date.setDate(today.getDate() - (6 - i));
                    dates.push(
                        date.toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: '2-digit' 
                        }).replace(' ', '-')
                    );
                }
                
                // Example data for top 3 sellers
                seriesData = [
                    {
                        name: "Tech Store",
                        data: [4500, 5200, 4800, 6100, 4900, 5300, 5800],
                        color: "#4e73df"
                    },
                    {
                        name: "Fashion Boutique",
                        data: [3200, 3800, 3500, 4200, 3900, 4100, 4500],
                        color: "#1cc88a"
                    },
                    {
                        name: "Electronics Hub",
                        data: [2800, 3200, 2900, 3500, 3100, 3400, 3800],
                        color: "#36b9cc"
                    }
                ];
            }
            
            // Create the chart
            const chartOptions = {
                series: seriesData,
                chart: {
                    height: 350,
                    type: "line",
                    toolbar: {
                        show: true
                    }
                },
                dataLabels: {
                    enabled: false
                },
                markers: {
                    size: 5,
                    hover: {
                        size: 7,
                        sizeOffset: 3
                    }
                },
                stroke: {
                    curve: "smooth",
                    width: 3
                },
                grid: {
                    borderColor: window.theme.gray300,
                    strokeDashArray: 4
                },
                xaxis: {
                    categories: dates,
                    labels: {
                        style: {
                            fontSize: "12px",
                            fontWeight: 400,
                            colors: window.theme.gray600,
                            fontFamily: '"Inter", "sans-serif"'
                        }
                    },
                    axisBorder: {
                        show: true,
                        color: window.theme.gray300,
                        height: 1
                    },
                    axisTicks: {
                        show: true,
                        color: window.theme.gray300,
                        height: 6
                    }
                },
                legend: {
                    position: "top",
                    horizontalAlign: "right",
                    floating: true,
                    offsetY: -25,
                    fontWeight: 600,
                    color: window.theme.gray600
                },
                yaxis: {
                    labels: {
                        formatter: function(value) {
                            return "Rs. " + value.toLocaleString('en-IN');
                        },
                        style: {
                            fontSize: "12px",
                            fontWeight: 400,
                            colors: window.theme.gray600,
                            fontFamily: '"Inter", "sans-serif"'
                        }
                    }
                },
                tooltip: {
                    shared: true,
                    intersect: false,
                    custom: function({ series, seriesIndex, dataPointIndex, w }) {
                        const dayIndex = dataPointIndex;
                        const dayLabel = dates[dayIndex];
                        
                        let tooltipHTML = `
                            <div style="padding: 16px; background: white; border: 1px solid ${window.theme.gray300}; border-radius: 8px; min-width: 320px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                <div style="font-weight: 700; margin-bottom: 12px; font-size: 14px; color: ${window.theme.gray800}; display: flex; align-items: center;">
                                    <i class="fas fa-calendar-day" style="margin-right: 8px; color: ${window.theme.primary};"></i>
                                    ${dayLabel}
                                </div>
                        `;
                        
                        // Calculate total for the day
                        let dayTotal = 0;
                        w.globals.series.forEach((sellerSeries) => {
                            dayTotal += sellerSeries[dayIndex];
                        });
                        
                        // Show total at the top
                        tooltipHTML += `
                            <div style="background: ${window.theme.primary}10; padding: 10px; border-radius: 6px; margin-bottom: 12px; border-left: 4px solid ${window.theme.primary};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 12px; color: ${window.theme.gray600}; font-weight: 600;">Platform Total:</span>
                                    <span style="color: ${window.theme.primary}; font-weight: 700; font-size: 16px;">
                                        Rs. ${dayTotal.toLocaleString('en-IN')}
                                    </span>
                                </div>
                            </div>
                        `;
                        
                        // Add each seller's data
                        tooltipHTML += `<div style="max-height: 200px; overflow-y: auto; padding-right: 4px;">`;
                        
                        // Sort sellers by amount (highest first)
                        const sellersForDay = w.globals.series.map((sellerSeries, idx) => {
                            return {
                                name: w.globals.seriesNames[idx] || `Seller ${idx + 1}`,
                                color: w.globals.colors[idx] || window.theme.gray500,
                                amount: sellerSeries[dayIndex]
                            };
                        }).sort((a, b) => b.amount - a.amount);
                        
                        sellersForDay.forEach((seller, idx) => {
                            if (seller.amount > 0) {
                                tooltipHTML += `
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid ${window.theme.gray100};">
                                        <div style="display: flex; align-items: center; flex: 1;">
                                            <div style="width: 10px; height: 10px; border-radius: 50%; background: ${seller.color}; margin-right: 10px;"></div>
                                            <span style="font-size: 13px; font-weight: 600; color: ${window.theme.gray700};">
                                                ${seller.name}
                                            </span>
                                        </div>
                                        <span style="font-weight: 700; font-size: 13px; color: ${window.theme.gray800};">
                                            Rs. ${seller.amount.toLocaleString('en-IN')}
                                        </span>
                                    </div>
                                `;
                            }
                        });
                        
                        tooltipHTML += `</div>`;
                        
                        // Calculate and show percentage for each seller
                        tooltipHTML += `<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid ${window.theme.gray200};">`;
                        tooltipHTML += `<div style="font-size: 12px; color: ${window.theme.gray600}; margin-bottom: 8px; font-weight: 600;">Market Share:</div>`;
                        
                        sellersForDay.forEach((seller, idx) => {
                            if (seller.amount > 0 && dayTotal > 0) {
                                const percentage = ((seller.amount / dayTotal) * 100).toFixed(1);
                                tooltipHTML += `
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                        <div style="display: flex; align-items: center;">
                                            <div style="width: 8px; height: 8px; border-radius: 50%; background: ${seller.color}; margin-right: 8px;"></div>
                                            <span style="font-size: 11px; color: ${window.theme.gray600};">${seller.name}</span>
                                        </div>
                                        <span style="font-size: 11px; font-weight: 600; color: ${window.theme.gray700};">${percentage}%</span>
                                    </div>
                                `;
                            }
                        });
                        
                        tooltipHTML += `</div>`;
                        
                        // Add summary
                        tooltipHTML += `
                            <div style="margin-top: 12px; padding: 10px; background: ${window.theme.gray100}; border-radius: 4px;">
                                <div style="display: flex; justify-content: space-between; font-size: 11px; color: ${window.theme.gray600};">
                                    <span>Sellers Active: <strong style="color: ${window.theme.gray700};">${sellersForDay.filter(s => s.amount > 0).length}</strong></span>
                                    <span>Total: <strong style="color: ${window.theme.gray700};">Rs. ${dayTotal.toLocaleString('en-IN')}</strong></span>
                                </div>
                            </div>
                        `;
                        
                        tooltipHTML += `</div>`;
                        
                        return tooltipHTML;
                    }
                }
            };
            
            const chart = new ApexCharts(document.getElementById("sellersChart"), chartOptions);
            chart.render();
            
            console.log("Sellers chart rendered successfully");
            
        } catch (error) {
            console.error("Error rendering sellers chart:", error);
            const chartContainer = document.getElementById("sellersChart");
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading sellers chart: ${error.message}
                    </div>
                `;
            }
        }
    }
    
})();