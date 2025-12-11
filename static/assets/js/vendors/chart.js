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
    
    var chartOptions;
    
    // SIMPLE function to get sales data
    function getSalesData() {
        try {
            // Get the script tag content
            const dataElement = document.getElementById('salesChartData');
            if (!dataElement) {
                console.log("No salesChartData element found");
                return null;
            }
            
            const jsonText = dataElement.textContent.trim();
            if (!jsonText) {
                console.log("salesChartData is empty");
                return null;
            }
            
            console.log("Raw JSON text:", jsonText);
            const data = JSON.parse(jsonText);
            console.log("Parsed sales data:", data);
            return data;
            
        } catch (error) {
            console.error("Error getting sales data:", error);
            console.error("Error at character:", error.position);
            return null;
        }
    }
    
    // Revenue Chart (Area Chart)
    if (document.getElementById("revenueChart")) {
        try {
            console.log("=== Initializing revenue chart ===");
            
            // Get sales data
            const salesData = getSalesData();
            let hasRealData = false;
            let chartLabels = [];
            let chartTotals = [];
            let chartBreakdown = {};
            
            if (salesData && salesData.daily_totals) {
                console.log("Checking sales data...");
                console.log("has_sales_data:", salesData.has_sales_data);
                console.log("daily_totals:", salesData.daily_totals);
                console.log("Some non-zero:", salesData.daily_totals.some(total => total > 0));
                
                // Check if we have real data
                hasRealData = salesData.has_sales_data && 
                             salesData.daily_totals.some(total => total > 0);
                
                if (hasRealData) {
                    console.log("We have real sales data!");
                    
                    // Filter to show only days with sales
                    chartLabels = [];
                    chartTotals = [];
                    chartBreakdown = {};
                    
                    salesData.date_labels.forEach((label, index) => {
                        if (salesData.daily_totals[index] > 0) {
                            chartLabels.push(label);
                            chartTotals.push(salesData.daily_totals[index]);
                            chartBreakdown[chartLabels.length - 1] = salesData.daily_breakdown[index.toString()] || [];
                        }
                    });
                    
                    console.log("Filtered - Labels:", chartLabels);
                    console.log("Filtered - Totals:", chartTotals);
                    console.log("Filtered - Breakdown:", chartBreakdown);
                }
            }
            
            // If no real data, use example
            if (!hasRealData || chartLabels.length === 0) {
                console.log("Using example data");
                
                // Generate example labels for last 7 days
                const today = new Date();
                chartLabels = [];
                for (let i = 0; i < 7; i++) {
                    const date = new Date(today);
                    date.setDate(today.getDate() - (6 - i)); // Start from 6 days ago
                    chartLabels.push(
                        date.toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: '2-digit' 
                        }).replace(' ', '-')
                    );
                }
                
                chartTotals = [600, 550, 700, 800, 750, 900, 850];
                // Example data with product names
                chartBreakdown = {
                    0: [
                        {name: "T-Shirt", price: 200},
                        {name: "Jeans", price: 300},
                        {name: "Shoes", price: 100},
                        {name: "Jacket", price: 400}
                    ],
                    1: [
                        {name: "T-Shirt", price: 250},
                        {name: "Jeans", price: 200},
                        {name: "Shoes", price: 100}
                    ],
                    2: [
                        {name: "T-Shirt", price: 300},
                        {name: "Jeans", price: 250},
                        {name: "Shoes", price: 150}
                    ],
                    3: [
                        {name: "T-Shirt", price: 400},
                        {name: "Jeans", price: 300},
                        {name: "Shoes", price: 100}
                    ],
                    4: [
                        {name: "T-Shirt", price: 350},
                        {name: "Jeans", price: 300},
                        {name: "Shoes", price: 100}
                    ],
                    5: [
                        {name: "T-Shirt", price: 500},
                        {name: "Jeans", price: 300},
                        {name: "Shoes", price: 100}
                    ],
                    6: [
                        {name: "T-Shirt", price: 450},
                        {name: "Jeans", price: 300},
                        {name: "Shoes", price: 100}
                    ]
                };
                
                hasRealData = false;
            }
            
            console.log("Final configuration - Real data:", hasRealData);
            console.log("Labels:", chartLabels);
            console.log("Totals:", chartTotals);
            
            // Create the chart
            chartOptions = {
                series: [{
                    name: hasRealData ? "Daily Sales" : "Example Sales",
                    data: chartTotals
                }],
                chart: {
                    height: 350,
                    type: "area",
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
                colors: hasRealData ? ["#0aad0a"] : [window.theme.gray500],
                stroke: {
                    curve: "smooth",
                    width: 3
                },
                fill: {
                    type: "gradient",
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.1,
                        stops: [0, 90, 100]
                    }
                },
                grid: {
                    borderColor: window.theme.gray300,
                    strokeDashArray: 4
                },
                xaxis: {
                    categories: chartLabels,
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
                    custom: function({ series, seriesIndex, dataPointIndex, w }) {
                        const dayIndex = dataPointIndex;
                        const dayLabel = chartLabels[dayIndex];
                        const totalSales = series[0][dayIndex];
                        const breakdown = chartBreakdown[dayIndex];

                        let itemsHTML = "";
                        if (breakdown && Array.isArray(breakdown) && breakdown.length > 0) {
                            // Group items by product name and price
                            const productGroups = {};
                            breakdown.forEach(item => {
                                // Handle both old format (just number) and new format (object)
                                let productName = 'Product';
                                let price = 0;
                                
                                if (typeof item === 'object' && item !== null && item.name !== undefined) {
                                    // New format: object with name and price
                                    productName = item.name || 'Product';
                                    price = item.price || 0;
                                } else {
                                    // Old format: just a number
                                    productName = 'Product';
                                    price = typeof item === 'number' ? item : 0;
                                }
                                
                                const key = `${productName}|${price.toFixed(2)}`;
                                if (!productGroups[key]) {
                                    productGroups[key] = {
                                        name: productName,
                                        price: price,
                                        count: 0
                                    };
                                }
                                productGroups[key].count += 1;
                            });
                            
                            const itemsArray = Object.values(productGroups);
                            itemsHTML = `
                                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid ${window.theme.gray200}">
                                    <div style="font-weight: 600; color: ${window.theme.gray700}; margin-bottom: 6px; font-size: 13px;">
                                        <i class="fas fa-shopping-cart" style="margin-right: 6px;"></i>Products Sold (${breakdown.length}):
                                    </div>
                                    <div style="max-height: 150px; overflow-y: auto; padding-right: 4px;">
                            `;
                            
                            itemsArray.forEach((product, idx) => {
                                const itemTotal = product.price * product.count;
                                itemsHTML += `
                                    <div style="padding: 6px 0; border-bottom: 1px solid ${window.theme.gray100};">
                                        <div style="font-weight: 600; font-size: 12px; color: ${window.theme.gray800}; margin-bottom: 2px;">
                                            ${product.name}
                                        </div>
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <span style="font-size: 11px; color: ${window.theme.gray600};">
                                                ${product.count} × Rs. ${product.price.toLocaleString('en-IN', {minimumFractionDigits: 2})}
                                            </span>
                                            <span style="font-weight: 600; font-size: 12px; color: ${window.theme.gray800};">
                                                Rs. ${itemTotal.toLocaleString('en-IN', {minimumFractionDigits: 2})}
                                            </span>
                                        </div>
                                    </div>
                                `;
                            });
                            
                            itemsHTML += `
                                    </div>
                                    <div style="display: flex; justify-content: space-between; margin-top: 8px; padding-top: 8px; border-top: 1px solid ${window.theme.gray200};">
                                        <span style="font-weight: 600; font-size: 12px; color: ${window.theme.gray700};">Total Items:</span>
                                        <span style="font-weight: 700; font-size: 12px; color: ${window.theme.gray800};">${breakdown.length}</span>
                                    </div>
                                </div>
                            `;
                        } else {
                            itemsHTML = `
                                <div style="margin-top: 12px; padding: 12px; background: ${window.theme.gray100}; border-radius: 4px; text-align: center;">
                                    <i class="fas fa-info-circle" style="color: ${window.theme.warning}; margin-right: 6px;"></i>
                                    <span style="font-size: 12px; color: ${window.theme.gray600};">No product details available</span>
                                </div>
                            `;
                        }

                        return `
                            <div style="padding: 16px; background: white; border: 1px solid ${window.theme.gray300}; border-radius: 8px; min-width: 280px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                                <div style="font-weight: 700; margin-bottom: 8px; font-size: 14px; color: ${window.theme.gray800}; display: flex; align-items: center;">
                                    <i class="fas fa-calendar-day" style="margin-right: 8px; color: ${window.theme.primary};"></i>
                                    ${dayLabel}
                                </div>
                                <div style="background: ${hasRealData ? 'rgba(10, 173, 10, 0.1)' : 'rgba(100, 116, 139, 0.1)'}; padding: 12px; border-radius: 6px; margin-bottom: 12px;">
                                    <div style="font-size: 12px; color: ${window.theme.gray600}; margin-bottom: 4px;">
                                        ${hasRealData ? 'Total Sales' : 'Example Sales'}
                                    </div>
                                    <div style="color: ${hasRealData ? window.theme.success : window.theme.gray600}; font-weight: 700; font-size: 18px;">
                                        Rs. ${totalSales.toLocaleString('en-IN')}
                                    </div>
                                </div>
                                ${itemsHTML}
                                ${!hasRealData ? `
                                    <div style="margin-top: 12px; padding: 8px; background: ${window.theme.warning}15; border: 1px solid ${window.theme.warning}30; border-radius: 4px;">
                                        <div style="display: flex; align-items: center;">
                                            <i class="fas fa-exclamation-triangle" style="color: ${window.theme.warning}; margin-right: 6px;"></i>
                                            <span style="font-size: 11px; color: ${window.theme.warning}; font-weight: 600;">Showing example data</span>
                                        </div>
                                    </div>
                                ` : ''}
                            </div>
                        `;
                    }
                }
            };
            
            const chart = new ApexCharts(document.getElementById("revenueChart"), chartOptions);
            chart.render();
            
            console.log("Chart rendered successfully");
            
            // Add status note
            setTimeout(() => {
                const chartContainer = document.getElementById("revenueChart");
                if (chartContainer) {
                    const noteDiv = document.createElement('div');
                    noteDiv.className = 'text-center mt-3';
                    noteDiv.style.fontSize = '12px'; 
                    
                    if (hasRealData) {
                        noteDiv.innerHTML = `
                            <span style="color: ${window.theme.success}; font-weight: 600;">
                                <i class="fas fa-check-circle me-1"></i>
                                Showing actual sales data for ${chartLabels.length} day${chartLabels.length > 1 ? 's' : ''}
                            </span>
                        `;
                    } else {
                        noteDiv.innerHTML = `
                            <span style="color: ${window.theme.warning}; font-weight: 600;">
                                <i class="fas fa-info-circle me-1"></i>
                                Showing example data (no sales recorded yet)
                            </span>
                        `;
                    }
                    
                    chartContainer.appendChild(noteDiv);
                }
            }, 100);
            
        } catch (error) {
            console.error("Error rendering revenue chart:", error);
            // Show error message
            const chartContainer = document.getElementById("revenueChart");
            if (chartContainer) {
                chartContainer.innerHTML = `
                    <div class="alert alert-danger" role="alert">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Error loading sales chart: ${error.message}
                    </div>
                `;
            }
        }
    }
    
    // Total Sales Chart (Donut Chart)
    if (document.getElementById("totalSale")) {
        chartOptions = {
            series: [6000, 2000, 1000, 600],
            labels: ["Product 1", "Product 2", "Product 3", "Product 4"],
            colors: ["#0aad0a", "#ffc107", "#db3030", "#016bf8"],
            chart: {
                type: "donut",
                height: 280
            },
            legend: {
                show: false
            },
            dataLabels: {
                enabled: false
            },
            plotOptions: {
                pie: {
                    donut: {
                        size: "85%",
                        background: "transparent",
                        labels: {
                            show: true,
                            name: {
                                show: true,
                                fontSize: "22px",
                                fontFamily: '"Inter", "sans-serif"',
                                fontWeight: 600,
                                colors: [window.theme.gray600],
                                offsetY: -10,
                                formatter: function(val) {
                                    return val;
                                }
                            },
                            value: {
                                show: true,
                                fontSize: "24px",
                                fontFamily: '"Inter", "sans-serif"',
                                fontWeight: 800,
                                colors: window.theme.gray800,
                                offsetY: 8,
                                formatter: function(val) {
                                    return "Rs. " + val;
                                }
                            },
                            total: {
                                show: true,
                                showAlways: false,
                                label: "Total Sales",
                                fontSize: "16px",
                                fontFamily: '"Inter", "sans-serif"',
                                fontWeight: 400,
                                colors: window.theme.gray400,
                                formatter: function(w) {
                                    const total = w.globals.seriesTotals.reduce((a, b) => a + b, 0);
                                    return "Rs. " + total;
                                }
                            }
                        }
                    }
                }
            },
            stroke: {
                width: 0
            },
            responsive: [
                {
                    breakpoint: 1400,
                    options: {
                        chart: {
                            type: "donut",
                            width: 290,
                            height: 330
                        }
                    }
                }
            ]
        };
        
        new ApexCharts(document.getElementById("totalSale"), chartOptions).render();
    }
})();