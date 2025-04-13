// (function($) {

// 	"use strict";

// 	var fullHeight = function() {

// 		$('.js-fullheight').css('height', $(window).height());
// 		$(window).resize(function(){
// 			$('.js-fullheight').css('height', $(window).height());
// 		});

// 	};
// 	fullHeight();

// 	 $('#sidebarCollapse').on('click', function () {
//         $('#sidebar').toggleClass('active');
//     });

// })(jQuery);

(function($) {
    "use strict";
    var fullHeight = function() {
        $('.js-fullheight').css('height', $(window).height());
        $(window).resize(function(){
            $('.js-fullheight').css('height', $(window).height());
        });
    };
    $(function() {
        fullHeight();
        // On page load, check screen size
        if ($(window).width() < 992) {
            $('#sidebar').removeClass('active'); // For mobile - add active class (collapsed)
        } else {
            $('#sidebar').addClass('active'); // For desktop - remove active class (expanded)
        }
        // Toggle sidebar on button click
        $('#sidebarCollapse').on('click', function () {
            $('#sidebar').toggleClass('active');
        });
    });
})(jQuery);


document.addEventListener('DOMContentLoaded', function () {
    // This only hides the loader when basic DOM is loaded
    setTimeout(function () {
        const loader = document.getElementById('loading-overlay');
        if (loader) {
            loader.classList.add('loaded');
        }
    }, 300); // Small delay for smoother transition
});

window.addEventListener('load', function () {
    // This ensures the loader is hidden when ALL resources are loaded
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.classList.add('loaded');
    }
});


// Start loader immediately — loader is already shown in HTML/CSS
document.addEventListener('DOMContentLoaded', function () {
    const loader = document.getElementById('loading-overlay');
    const sidebar = document.getElementById('sidebar');
    const navLinks = document.querySelectorAll('#sidebar .nav-link');

    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            // Prevent default navigation
            e.preventDefault();

            // Show loader immediately
            if (loader) {
                loader.classList.remove('loaded');
            }

            // Close sidebar
            if (sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
            }

            // Wait a bit so animation is visible, then go to the link
            setTimeout(() => {
                window.location.href = this.href;
            }, 300);
        });
    });
});

// Hide loader after all content (images/scripts) loads
window.addEventListener('load', function () {
    const loader = document.getElementById('loading-overlay');
    if (loader) {
        loader.classList.add('loaded');
    }
});



function copyToClipboard() {
    var copyText = document.getElementById("copyText");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices
    navigator.clipboard.writeText(copyText.value);

    // Show toast message
    var toastEl = document.getElementById('copyToast');
    var toast = new bootstrap.Toast(toastEl);
    toast.show();
}


function copyWalletId() {
    var walletId = document.getElementById("walletId");
    copyText.select();
    copyText.setSelectionRange(0, 99999); // For mobile devices
    navigator.clipboard.writeText(walletId.value);

    // Show toast message
    Toastify({
        text: "Wallet ID copied successfully!",
        duration: 3000,
        gravity: "top", // Position: top, bottom
        position: "right", // Left, center, right
        backgroundColor: "linear-gradient(to right, #4CAF50, #2E8B57)",
        className: "custom-toast",
        stopOnFocus: true
    }).showToast();
}



document.addEventListener("DOMContentLoaded", function () {
    const amountInput = document.getElementById("amount");
    const paymentMethodSelect = document.getElementById("payment-method");
    const paymentDetailsDiv = document.getElementById("payment-details");
    const paymentInfo = document.getElementById("payment-info");
    const proceedButton = document.getElementById("proceed-button");
    const confirmButton = document.getElementById("confirm-button");
    const paymentMethod = document.getElementById("payment-method").value;

    paymentMethodSelect.addEventListener("change", async function () {
        const selectedMethod = paymentMethodSelect.value;
        const depositAmount = amountInput.value.trim();
        if (!depositAmount) {
            showToast("⚠️ Please enter a deposit amount.");
            return;
        }
        if (!selectedMethod) {
            showToast("⚠️ Please select a payment method.");
            paymentDetailsDiv.style.display = "none";
            return;
        }

        if (!paymentMethod) {
            alert("Please select a payment method.");
            event.preventDefault(); // Stop form submission
        }

        // Show loading animation
        paymentInfo.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mt-2">Fetching payment details...</p>
            </div>
        `;
        paymentDetailsDiv.style.display = "block";

        try {
            const response = await fetch('/user/get_payment_details', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ method: selectedMethod })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }

            const data = await response.json();
            
            // Populate payment details
            paymentInfo.innerHTML = `
                <div class="p-4 border rounded bg-white shadow-sm" style="max-width: 500px; margin: auto;">
                    <h5 class="mb-3 text-primary text-center">Payment Details</h5>
                    <div class="d-flex flex-column gap-3">
                        <div style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Details:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="text-muted m-0">${data.details || 'N/A'}</p>
                        </div>

                        ${data.account_name ? `<div style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Account Name:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="m-0">${data.account_name}</p>
                        </div>` : ""}

                        ${data.account_number ? `<div style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Account Number:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="m-0">${data.account_number}</p>
                        </div>` : ""}

                        ${data.bank_name ? `<div style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Bank Name:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="m-0">${data.bank_name}</p>
                        </div>` : ""}

                        ${data.wallet_address ? `<div class="" style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Wallet Address:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="text-monospace mt-1">${data.wallet_address}</p>
                        </div>` : ""}

                        ${data.memo ? `<div class="" style="height: 40px; padding: 7px 0; margin-top: 10px;">
                            <strong>Memo:</strong>
                            <p style="height: 20px; padding: 12px 0;" class="mt-1">${data.memo}</p>
                        </div>` : ""}

                        ${data.image_url ? `<div class="text-center mt-3">
                            <img src="${data.image_url}" alt="Payment QR" class="img-fluid rounded shadow-sm" style="max-width: 200px;">
                        </div>` : ""}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Fetch error:', error);
            paymentInfo.innerHTML = `
                <div class="alert alert-danger text-center p-3" role="alert">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        }
    });

    proceedButton.addEventListener("click", function () {
        document.getElementById("modal-note").style.display = "block";

        // Hide Proceed button and show Confirm button
        proceedButton.style.display = "none";
        confirmButton.style.display = "block";

        // const fileInput = document.createElement("input");
        // fileInput.type = "file";
        // fileInput.id = "payment-proof";
        // fileInput.className = "form-control";
        // fileInput.accept = "image/*";
        // if (!document.getElementById("payment-proof")) {
        //     document.getElementById("payment-details").appendChild(fileInput);
        // }
    });
});


document.addEventListener('DOMContentLoaded', function() {
    // Event listener for the edit button
    const editButtons = document.querySelectorAll('.edit-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Get transaction data from button's data attributes
            const transactionId = event.target.closest('button').getAttribute('data-transaction-id');
            const transactionType = event.target.closest('button').getAttribute('data-transaction-type');
            const transactionDetail = event.target.closest('button').getAttribute('data-transaction-detail');
            const amount = event.target.closest('button').getAttribute('data-amount');
            const status = event.target.closest('button').getAttribute('data-status');
            const imageUrl = event.target.closest('button').getAttribute('data-image-url');  // Get image URL

            // Populate the modal with the transaction data
            document.getElementById('transactionId').value = transactionId;
            document.getElementById('transactionType').value = transactionType;
            document.getElementById('transactionDetail').value = transactionDetail;
            document.getElementById('amount').value = amount;
            document.getElementById('status').value = status;

            // Check if the image_url exists and display it
            const imageSection = document.getElementById('imageSection');
            const imagePreview = document.getElementById('imagePreview');
            if (imageUrl) {
                imageSection.style.display = 'block';
                imagePreview.src = imageUrl;
            } else {
                imageSection.style.display = 'none';
            }

            // Show the modal
            $('#editTransactionModal').modal('show');
        });
    });
});




function copyWalletId() {
    var walletInput = document.getElementById("walletId");
    walletInput.select();
    document.execCommand("copy");
    alert("Wallet ID copied: " + walletInput.value);
}

document.addEventListener("DOMContentLoaded", function () {
    const proceedButton = document.getElementById("proceed-button");
    const confirmButton = document.getElementById("confirm-button");
    const proofUpload = document.getElementById("proof-upload");
    const depositForm = document.getElementById("deposit-form");

    proceedButton.addEventListener("click", function () {
        proofUpload.style.display = "block";  
        proceedButton.style.display = "none";  
        confirmButton.style.display = "block"; 
    });

    confirmButton.addEventListener("click", function () {
        depositForm.submit();  // Manually submit the form when Confirm is clicked
    });
});



// Function to show toast messages
function showToast(message) {
    var toastEl = document.getElementById("depositToast");
    var toastBody = toastEl.querySelector(".toast-body");
    toastBody.textContent = message;

    var toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// Withdrawal Modal
// document.addEventListener("DOMContentLoaded", function () {
//     const withdrawButton = document.querySelector(".funds__cards.bg-primary a");
//     withdrawButton.addEventListener("click", function (event) {
//         event.preventDefault(); // Prevent default link behavior

//         // Dummy BTC data (Replace with real data)
//         const btcWallet = "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh";
//         const memo = "Withdrawal for February";
//         const amount = "0.05 BTC";
//         const qrCodeSrc = "https://www.bitcoinqrcodemaker.com/api/?style=bitcoin&address=" + btcWallet; // Example QR code

//         // Populate modal fields
//         document.getElementById("btcWallet").value = btcWallet;
//         document.getElementById("memo").value = memo;
//         document.getElementById("withdrawAmount").value = amount;
//         document.getElementById("qrCode").src = qrCodeSrc;
//         document.getElementById("qrCode").style.display = "block"; // Show QR code
//     });
// });


// Tranfer Modal
document.addEventListener("DOMContentLoaded", function () {
    const transferButton = document.querySelector(".funds__cards a");
    transferButton.addEventListener("click", function (event) {
        event.preventDefault(); // Prevent default link behavior

        // Dummy user data (Replace with real data)
        const userEmail = "user@example.com";
        const walletID = "WALLET-123456";
        const amount = "$100";

        // Populate modal fields
        document.getElementById("userEmail").value = userEmail;
        document.getElementById("walletID").value = walletID;
        document.getElementById("transferAmount").value = amount;
    });
});


function togglePaymentFields() {
    let selectedMethod = document.getElementById("payment-method").value;
    document.getElementById("bank-fields").classList.add("d-none");
    document.getElementById("crypto-fields").classList.add("d-none");
    document.getElementById("qr-code-field").classList.add("d-none");

    if (selectedMethod === "bank_transfer") {
        document.getElementById("bank-fields").classList.remove("d-none");
    } else if (selectedMethod === "bitcoin") {
        document.getElementById("crypto-fields").classList.remove("d-none");
        document.getElementById("qr-code-field").classList.remove("d-none");
    }
}


function openEditModal(payment) {
    console.log("Payment data received:", payment); // Debugging

    // Safely set form values if elements exist
    let setValue = (id, value) => {
        let el = document.getElementById(id);
        if (el) el.value = value || "";
    };

    setValue('edit-payment-id', payment.id);
    setValue('edit-method', payment.method);
    setValue('edit-details', payment.details);
    setValue('edit-account-number', payment.account_number);
    setValue('edit-bank-name', payment.bank_name);
    setValue('edit-account-name', payment.account_name);
    setValue('edit-wallet-address', payment.wallet_address);
    setValue('edit-memo', payment.memo);
    setValue('edit-network-address', payment.network_address);

    // Handle image preview
    let imagePreview = document.getElementById('edit-image-preview');
    if (imagePreview) {
        if (payment.image_url) {
            imagePreview.src = payment.image_url;
            imagePreview.style.display = "block";
        } else {
            imagePreview.style.display = "none";
        }
    }

    // Show the modal
    let editModal = new bootstrap.Modal(document.getElementById('editPaymentModal'));
    editModal.show();
}


document.addEventListener("DOMContentLoaded", function () {
    const editButtons = document.querySelectorAll(".edit-plan-btn");

    editButtons.forEach(button => {
        button.addEventListener("click", function () {
            // Get plan details from button attributes
            const planId = this.getAttribute("data-plan-id");
            const planName = this.getAttribute("data-plan-name");
            const planRoi = this.getAttribute("data-plan-roi");
            const planMin = this.getAttribute("data-plan-min");
            const planMax = this.getAttribute("data-plan-max");
            const planDuration = this.getAttribute("data-plan-duration");
            const planCapital = this.getAttribute("data-plan-capital");

            // Set modal fields
            document.getElementById("edit-plan-id").value = planId;
            document.getElementById("edit-plan-name").value = planName;
            document.getElementById("edit-plan-roi").value = planRoi;
            document.getElementById("edit-plan-min").value = planMin;
            document.getElementById("edit-plan-max").value = planMax;
            document.getElementById("edit-plan-duration").value = planDuration;
            document.getElementById("edit-plan-capital").value = planCapital;

            // Update the form action URL dynamically
            document.getElementById("editPlanForm").action = `/admin/edit_plan/${planId}`;
        });
    });
});


document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-plan-btn").forEach(button => {
        button.addEventListener("click", function () {
            let planId = this.getAttribute("data-plan-id");

            Swal.fire({
                title: "Are you sure?",
                text: "You won't be able to revert this!",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#d33",
                cancelButtonColor: "#3085d6",
                confirmButtonText: "Yes, delete it!"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = `/admin/delete_plan/${planId}`;
                }
            });
        });
    });
});


AOS.init({
  duration: 1200,
})




