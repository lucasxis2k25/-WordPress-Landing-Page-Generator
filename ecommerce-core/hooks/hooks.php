<?php
/**
 * DemoStore Core - Hooks customizados
 *
 * Hooks de validação, segurança e integrações automáticas.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

/**
 * HOOK 1: Validação "Zero Inferência" (Action: save_post)
 * 
 * Este hook verifica se o produto que está sendo salvo tem os campos obrigatórios 
 * do ACF preenchidos de forma correta (baseado nas regras de copy e SEO B2B).
 * Caso 'sp_resumo_tecnico' esteja vazio, ele registra um erro (log), garantindo 
 * que a integridade seja rastreada.
 */
add_action( 'save_post_product', 'DemoStore_validate_zero_inference_rules', 10, 3 );
function DemoStore_validate_zero_inference_rules( $post_id, $post, $update ) {
    // Evita loop infinito ou execução em auto-saves
    if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) return;
    if ( wp_is_post_revision( $post_id ) ) return;

    $resumo = get_post_meta( $post_id, 'sp_resumo_tecnico', true );
    
    // Regra: O resumo técnico não pode ser vazio. Se estiver, registra um alerta de auditoria.
    if ( empty( $resumo ) ) {
        error_log( "[Sell-Parts Zero Inferência] ALERTA: O produto ID {$post_id} ({$post->post_title}) foi salvo sem o 'sp_resumo_tecnico'. Verifique o pipeline do gerador ACF." );
    }
}

/**
 * HOOK 2: Fallback de renderização no WooCommerce (Action: woocommerce_after_single_product_summary)
 * 
 * Se por algum motivo o Elementor falhar ou a página não usar o Single Product Template,
 * este hook garante que os blocos essenciais da Sell-Parts sejam exibidos na página do produto.
 */
add_action( 'woocommerce_after_single_product_summary', 'DemoStore_fallback_elementor_render', 15 );
function DemoStore_fallback_elementor_render() {
    // Verifica se a página está usando o Elementor. 
    // Se estiver, os shortcodes já foram inseridos via Template Builder.
    if ( class_exists( '\Elementor\Plugin' ) ) {
        $document = \Elementor\Plugin::$instance->documents->get( get_the_ID() );
        if ( $document && $document->is_built_with_elementor() ) {
            return; // Já usa elementor, não faz nada
        }
    }

    echo '<div class="sp-fallback-container" style="margin-top:40px; padding: 20px; border-top: 1px solid #eee;">';
    echo '<h3>Especificações Técnicas</h3>';
    echo do_shortcode( '[sp_especificacoes]' );
    
    echo '<h3 style="margin-top:20px;">Aplicações Comuns</h3>';
    echo do_shortcode( '[sp_aplicacoes]' );
    
    echo '<h3 style="margin-top:20px;">Dúvidas Frequentes (FAQ)</h3>';
    echo do_shortcode( '[sp_faq]' );
    echo '</div>';
}
