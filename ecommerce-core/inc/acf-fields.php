<?php
/**
 * DemoStore Core - Registro dos Campos ACF
 *
 * Grupo: SP - Landing Page Produto
 * Condição: Post Type = product (WooCommerce)
 *
 * Campos:
 *   sp_resumo_tecnico   → Área de texto
 *   sp_especificacoes   → Editor WYSIWYG
 *   sp_aplicacoes       → Editor WYSIWYG
 *   sp_beneficios       → Editor WYSIWYG
 *   sp_diferenciais     → Editor WYSIWYG
 *   sp_downloads        → Editor WYSIWYG
 *   sp_faq              → Editor WYSIWYG
 *   sp_alerta_tecnico   → Área de texto
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// Os campos serão registrados via ACF UI no WordPress.
// Este arquivo serve como documentação e backup.
// Se preferir registrar via código PHP (sem depender da UI), descomente abaixo.

/*
add_action( 'acf/init', function() {
    if ( ! function_exists( 'acf_add_local_field_group' ) ) return;

    acf_add_local_field_group( array(
        'key'      => 'group_sp_landing_page',
        'title'    => 'SP - Landing Page Produto',
        'fields'   => array(
            array( 'key' => 'field_sp_resumo',       'label' => 'Resumo Técnico',          'name' => 'sp_resumo_tecnico',  'type' => 'textarea', 'rows' => 4 ),
            array( 'key' => 'field_sp_specs',        'label' => 'Especificações Técnicas', 'name' => 'sp_especificacoes',  'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 0 ),
            array( 'key' => 'field_sp_apps',         'label' => 'Aplicações',              'name' => 'sp_aplicacoes',      'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 0 ),
            array( 'key' => 'field_sp_benefits',     'label' => 'Benefícios',              'name' => 'sp_beneficios',      'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 0 ),
            array( 'key' => 'field_sp_diferenciais', 'label' => 'Diferenciais',            'name' => 'sp_diferenciais',    'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 0 ),
            array( 'key' => 'field_sp_downloads',    'label' => 'Downloads',               'name' => 'sp_downloads',       'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 1 ),
            array( 'key' => 'field_sp_faq',          'label' => 'FAQ',                     'name' => 'sp_faq',             'type' => 'wysiwyg',  'tabs' => 'all', 'toolbar' => 'full', 'media_upload' => 0 ),
            array( 'key' => 'field_sp_alerta',       'label' => 'Alerta Técnico',          'name' => 'sp_alerta_tecnico',  'type' => 'textarea', 'rows' => 3 ),
        ),
        'location' => array(
            array(
                array( 'param' => 'post_type', 'operator' => '==', 'value' => 'product' ),
            ),
        ),
        'position'  => 'normal',
        'style'     => 'default',
        'menu_order' => 0,
    ));
});
*/
