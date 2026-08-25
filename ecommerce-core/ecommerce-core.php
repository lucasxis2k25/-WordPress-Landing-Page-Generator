<?php
/**
 * Plugin Name: DemoStore Core
 * Description: Plugin principal da Demo Store - Campos ACF, Shortcodes e Schema JSON-LD para Landing Pages B2B.
 * Version: 1.0.0
 * Author: Demo Store
 * Text Domain: DemoStore-core
 */

if ( ! defined( 'ABSPATH' ) ) exit;

define( 'SP_CORE_VERSION', '1.0.0' );
define( 'SP_CORE_PATH', plugin_dir_path( __FILE__ ) );
define( 'SP_CORE_URL', plugin_dir_url( __FILE__ ) );

// Carregar módulos
require_once SP_CORE_PATH . 'inc/acf-fields.php';
require_once SP_CORE_PATH . 'inc/shortcodes.php';
require_once SP_CORE_PATH . 'inc/schema.php';
require_once SP_CORE_PATH . 'hooks/hooks.php';

// Carregar CSS frontend
add_action( 'wp_enqueue_scripts', function() {
    if ( is_product() ) {
        wp_enqueue_style(
            'DemoStore-css',
            SP_CORE_URL . 'assets/css/DemoStore.css',
            array(),
            SP_CORE_VERSION
        );
    }
});
