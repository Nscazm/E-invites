document.getElementById('inviteForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('inviteName').value;
    const email = document.getElementById('inviteEmail').value;

    fetch('/admin/invite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `name=${encodeURIComponent(name)}&email=${encodeURIComponent(email)}`
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
});
