// MiniStore — hieu ung giao dien (khong anh huong logic nghiep vu/bao mat)
document.addEventListener("DOMContentLoaded", function () {
  // 1) Fade-in toan trang khi tai xong
  requestAnimationFrame(function () {
    document.body.classList.add("ms-loaded");
  });

  // 2) Hieu ung "scroll reveal": cac the .ms-reveal xuat hien khi cuon toi
  var revealEls = document.querySelectorAll(".ms-reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("ms-in-view");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach(function (el) {
      io.observe(el);
    });
  } else {
    revealEls.forEach(function (el) {
      el.classList.add("ms-in-view");
    });
  }

  // 3) Header them bong do khi cuon trang
  var header = document.querySelector(".ms-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("ms-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // 4) Hieu ung gon song (ripple) khi bam nut .ms-btn
  document.querySelectorAll(".ms-btn").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      var rect = btn.getBoundingClientRect();
      var ripple = document.createElement("span");
      var size = Math.max(rect.width, rect.height);
      ripple.className = "ms-ripple";
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = e.clientX - rect.left - size / 2 + "px";
      ripple.style.top = e.clientY - rect.top - size / 2 + "px";
      btn.appendChild(ripple);
      setTimeout(function () {
        ripple.remove();
      }, 600);
    });
  });

  // 5) Hien spinner nho tren nut Submit khi gui form (UX, khong chan submit)
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector(".ms-btn");
      if (btn) btn.classList.add("ms-loading");
    });
  });
});
