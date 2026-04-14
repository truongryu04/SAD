function initStaffCommonUI(options) {
    var config = options || {};
    var sidebar = document.getElementById("sidebar");
    var sidebarBackdrop = document.getElementById("sidebarBackdrop");
    var menuToggle = document.getElementById("menuToggle");
    var profileTrigger = document.getElementById("profileTrigger");
    var profileMenu = document.getElementById("profileMenu");

    if (menuToggle && sidebar && sidebarBackdrop) {
        menuToggle.addEventListener("click", function () {
            sidebar.classList.toggle("open");
            sidebarBackdrop.classList.toggle("show");
        });

        sidebarBackdrop.addEventListener("click", function () {
            sidebar.classList.remove("open");
            sidebarBackdrop.classList.remove("show");
        });
    }

    if (profileTrigger && profileMenu) {
        profileTrigger.addEventListener("click", function () {
            profileMenu.classList.toggle("show");
        });

        profileTrigger.addEventListener("keydown", function (event) {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                profileMenu.classList.toggle("show");
            }
        });

        document.addEventListener("click", function (event) {
            if (!event.target.closest(".header-actions")) {
                profileMenu.classList.remove("show");
            }
        });
    }

    if (config.navMenuId) {
        var navMenu = document.getElementById(config.navMenuId);
        if (navMenu) {
            navMenu.addEventListener("click", function (event) {
                var button = event.target.closest("button.nav-link");
                if (!button) {
                    return;
                }

                navMenu.querySelectorAll("button.nav-link").forEach(function (item) {
                    item.classList.remove("active");
                });
                button.classList.add("active");

                if (window.innerWidth <= 860 && sidebar && sidebarBackdrop) {
                    sidebar.classList.remove("open");
                    sidebarBackdrop.classList.remove("show");
                }
            });
        }
    }
}

window.initStaffCommonUI = initStaffCommonUI;
