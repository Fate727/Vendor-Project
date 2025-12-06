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
    
    // Revenue Chart (Area Chart)
    if (document.getElementById("revenueChart")) {
        // Define individual product amounts for each month using numeric indices
        const monthlyBreakdown = {
            0: [200, 300, 100, 400],  // Jan
            1: [250, 200, 100],  // Feb
            2: [300, 250, 150],  // Mar
            3: [400, 300, 100],  // Apr
            4: [350, 300, 100],  // May
            5: [500, 300, 100],  // Jun
            6: [450, 300, 100]   // Jul
        };

        // Month names for display
        const monthNames = ["Jan-1", "Feb", "Mar", "Apr", "May", "Jun", "Jul"];

        console.log("Monthly Breakdown Data:", monthlyBreakdown); // Debug log

        chartOptions = {
            series: [
                {
                    name: "Total Income",
                    data: [600, 550, 700, 800, 750, 900, 850]
                }
            ],
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
                    size: 6,
                    sizeOffset: 3
                }
            },
            colors: ["#0aad0a"],
            stroke: {
                curve: "smooth",
                width: 2
            },
            grid: {
                borderColor: window.theme.gray300
            },
            xaxis: {
                categories: ["Jan-1", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
                labels: {
                    show: true,
                    align: "right",
                    minWidth: 0,
                    maxWidth: 160,
                    style: {
                        fontSize: "12px",
                        fontWeight: 400,
                        colors: [window.theme.gray600],
                        fontFamily: '"Inter", "sans-serif"'
                    }
                },
                axisBorder: {
                    show: true,
                    color: window.theme.gray300,
                    height: 1,
                    width: "100%",
                    offsetX: 0,
                    offsetY: 0
                },
                axisTicks: {
                    show: true,
                    borderType: "solid",
                    color: window.theme.gray300,
                    height: 6,
                    offsetX: 0,
                    offsetY: 0
                }
            },
            legend: {
                position: "top",
                fontWeight: 600,
                color: window.theme.gray600,
                markers: {
                    width: 8,
                    height: 8,
                    strokeWidth: 0,
                    strokeColor: "#fff",
                    fillColors: undefined,
                    radius: 12,
                    customHTML: undefined,
                    onClick: undefined,
                    offsetX: 0,
                    offsetY: 0
                },
                labels: {
                    colors: window.theme.gray600,
                    useSeriesColors: false
                }
            },
            yaxis: {
                labels: {
                    formatter: function(value) {
                        return value;
                    },
                    show: true,
                    align: "right",
                    minWidth: 0,
                    maxWidth: 160,
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
                    const monthIndex = dataPointIndex;
                    const monthName = monthNames[monthIndex];
                    const totalIncome = series[0][dataPointIndex];
                    
                    console.log("Tooltip - Month Index:", monthIndex, "Month Name:", monthName); // Debug log
                    
                    // Get breakdown data for this specific month using the index
                    const breakdown = monthlyBreakdown[monthIndex];
                    console.log("Tooltip - Breakdown data for index", monthIndex + ":", breakdown); // Debug log
                    
                    let soldItemsString = "No data";
                    if (breakdown && Array.isArray(breakdown) && breakdown.length > 0) {
                        soldItemsString = `{${breakdown.map(item => `'${item}'`).join(',')}}`;
                        console.log("Tooltip - Generated string:", soldItemsString); // Debug log
                    } else {
                        console.log("Tooltip - No breakdown data found for index", monthIndex); // Debug log
                    }
                    
                    return `
                        <div style="padding: 10px; background: white; border: 1px solid #ccc; border-radius: 5px; min-width: 200px;">
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">${monthName}</div>
                            <div style="color: #0aad0a; margin-bottom: 6px; font-weight: 600;">Total Income: ${totalIncome}</div>
                            <div style="margin-top: 8px; font-weight: 600; border-top: 1px solid #eee; padding-top: 8px;">Sold Items:</div>
                            <div style="font-family: monospace; background: #f8f9fa; padding: 8px; border-radius: 4px; margin-top: 4px; border: 1px solid #e9ecef;">
                                ${soldItemsString}
                            </div>
                        </div>
                    `;
                }
            }
        };
        
        new ApexCharts(document.getElementById("revenueChart"), chartOptions).render();
    }
    

    // Total Sales Chart (Donut Chart)
    if (document.getElementById("totalSale")) {
        chartOptions = {
            series: [6000, 2000, 1000, 600],
            labels: ["Prodcut 1", "Prodcut 2", "Prodcut 3", "Prodcut 4"],
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
                                    return val;
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
                                    return w.globals.seriesTotals.reduce((a, b) => a + b, 0);
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