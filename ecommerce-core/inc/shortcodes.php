<?php
/**
 * DemoStore Core - Shortcodes para os blocos da Landing Page
 *
 * Cada shortcode busca o campo ACF do produto atual e renderiza o HTML.
 * O Elementor Single Product Template usa o widget "Shortcode" para exibir.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// [sp_resumo_tecnico]
add_shortcode( 'sp_resumo_tecnico', function() {
    $value = get_field( 'sp_resumo_tecnico', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-resumo-tecnico"><p>' . esc_html( $value ) . '</p></div>';
});

// [sp_especificacoes]
add_shortcode( 'sp_especificacoes', function() {
    $value = get_field( 'sp_especificacoes', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-especificacoes">' . wp_kses_post( $value ) . '</div>';
});

// [sp_aplicacoes]
add_shortcode( 'sp_aplicacoes', function() {
    $value = get_field( 'sp_aplicacoes', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-aplicacoes">' . wp_kses_post( $value ) . '</div>';
});

// [sp_beneficios]
add_shortcode( 'sp_beneficios', function() {
    $value = get_field( 'sp_beneficios', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-beneficios">' . wp_kses_post( $value ) . '</div>';
});

// [sp_diferenciais]
add_shortcode( 'sp_diferenciais', function() {
    $value = get_field( 'sp_diferenciais', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-diferenciais">' . wp_kses_post( $value ) . '</div>';
});

// [sp_downloads]
add_shortcode( 'sp_downloads', function() {
    $value = get_field( 'sp_downloads', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-downloads">' . wp_kses_post( $value ) . '</div>';
});

// [sp_faq]
add_shortcode( 'sp_faq', function() {
    $value = get_field( 'sp_faq', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-faq">' . wp_kses_post( $value ) . '</div>';
});

// [sp_alerta_tecnico]
add_shortcode( 'sp_alerta_tecnico', function() {
    $value = get_field( 'sp_alerta_tecnico', get_the_ID() );
    if ( ! $value ) return '';
    return '<div class="sp-alerta-tecnico"><strong>⚠ Aviso de Engenharia:</strong> ' . esc_html( $value ) . '</div>';
});
