console.log("admin.js loaded");


// ==========================
// Dashboard Chart
// ==========================

const ctx = document.getElementById("appointmentChart");

if (ctx && window.chartData) {

    new Chart(ctx, {

        type: "bar",

        data: {

            labels: [

                "Pending",
                "Approved",
                "Completed",
                "Cancelled"

            ],

            datasets: [{

                label: "Appointments",

                data: [

                    window.chartData.pending,
                    window.chartData.approved,
                    window.chartData.completed,
                    window.chartData.cancelled

                ],

                borderWidth: 1

            }]

        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    display: false

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}



// ==========================
// Profile Menu
// ==========================

const profile = document.getElementById("profileMenu");


if(profile){

    profile.addEventListener("click", () => {

        profile.classList.toggle("active");

    });

}



// ==========================
// Doctor Live Search
// ==========================


