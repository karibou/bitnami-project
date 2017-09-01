<?php
// cli.php script
// Wordpress silent install

if ($db=($GLOBALS["___mysqli_ston"] = mysqli_connect("mariadb", "wordpress", "my-password", null, 3306))) {

    define('WP_INSTALLING', true);
    if (!file_exists('/app/wp-config.php')) {
        require_once('/app/wp-includes/functions.php');
    }
    require_once('/app/wp-config.php');
    require_once('/app/wp-admin/upgrade-functions.php');

    $weblog_title = stripslashes("My Bitnami Project");
    $admin_email = stripslashes("bouchard.louis@gmail.com");
    $user = stripslashes('caribou');
    $result = wp_install($weblog_title,$user,$admin_email,1);
    extract($result, EXTR_SKIP);


    ((bool)mysqli_query($db, "USE " . WORDPRESS_DATABASE));
    mysqli_query($GLOBALS["___mysqli_ston"], "UPDATE wp_users SET user_pass = MD5('WORDPRESS_USER_PASSWORD') WHERE wp_users.ID=1 LIMIT 1");
    mysqli_query($GLOBALS["___mysqli_ston"], "UPDATE wp_options SET option_value = 'WORDPRESS_URL' WHERE wp_options.option_name = 'siteurl'");
    mysqli_query($GLOBALS["___mysqli_ston"], "UPDATE wp_options SET option_value = 'WORDPRESS_URL' WHERE wp_options.option_name = 'home'");

    ((is_null($___mysqli_res = mysqli_close($db))) ? false : $___mysqli_res);
    echo('Your Wordpress installation is now configured.');
}
else {
    die('Connection failed. Make sure that the database server is running.');
}
