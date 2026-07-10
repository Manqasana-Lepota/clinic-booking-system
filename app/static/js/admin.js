console.log("admin.js loaded");


// ==========================
// Dashboard Chart
// ==========================

const ctx = document.getElementById('appointmentChart');

if (ctx) {

    new Chart(ctx, {

        type: 'line',

        data: {

            labels: [
                'Mon',
                'Tue',
                'Wed',
                'Thu',
                'Fri',
                'Sat',
                'Sun'
            ],

            datasets: [{

                label: 'Appointments',

                data: [12,19,8,15,25,18,20],

                borderWidth:3,
                fill:false

            }]

        },

        options: {

            responsive:true

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


