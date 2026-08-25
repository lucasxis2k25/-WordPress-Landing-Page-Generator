<?php
/**
 * DemoStore Core - Gerador automático de Schema JSON-LD
 *
 * Injeta Product Schema e FAQPage Schema no <head> de cada página de produto.
 * Dados puxados dos campos nativos do WooCommerce + ACF.
 */

if ( ! defined( 'ABSPATH' ) ) exit;

add_action( 'wp_head', function() {
    if ( ! is_product() ) return;

    global $product;
    if ( ! $product ) return;

    // Se houver o Schema pré-gerado pelo pipeline Python no custom field, usa ele diretamente
    $custom_product_schema = get_field('sp_schema_product', $product->get_id());
    if ( ! empty( $custom_product_schema ) ) {
        // Garantir que seja impresso como script JSON-LD limpo
        echo '<script type="application/ld+json">' . $custom_product_schema . '</script>' . "\n";
    } else {
        // Fallback dinâmico nativo do plugin
        $schema_product = array(
            '@context'    => 'https://schema.org/',
            '@type'       => 'Product',
            'name'        => $product->get_name(),
            'description' => wp_strip_all_tags( $product->get_short_description() ),
            'sku'         => $product->get_sku(),
            'mpn'         => $product->get_sku(),
            'brand'       => array( '@type' => 'Brand', 'name' => 'Demo Store' ),
            'offers'      => array(
                '@type'         => 'Offer',
                'url'           => get_permalink(),
                'priceCurrency' => 'BRL',
                'availability'  => 'https://schema.org/InStock',
                'seller'        => array( '@type' => 'Organization', 'name' => 'Demo Store' ),
            ),
        );

        $image_id = $product->get_image_id();
        if ( $image_id ) {
            $schema_product['image'] = array( wp_get_attachment_url( $image_id ) );
        }

        echo '<script type="application/ld+json">' . wp_json_encode( $schema_product, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) . '</script>' . "\n";
    }

    // FAQ Schema (se o campo ACF sp_faq existir)
    // O script gerador Python insere o HTML do FAQ com tags padrão.
    $faq_html = get_field('sp_faq', $product->get_id());
    
    if ( ! empty( $faq_html ) ) {
        $faq_schema = array(
            '@context'   => 'https://schema.org',
            '@type'      => 'FAQPage',
            'mainEntity' => array()
        );

        // Expressão regular para capturar blocos de perguntas e respostas.
        // Assumindo que o Python gera algo como <h3>Pergunta</h3> e <p>Resposta</p> ou <div class="faq-item">...
        // Faremos um parse genérico ou podemos usar DOMDocument.
        $dom = new DOMDocument();
        @$dom->loadHTML( mb_convert_encoding( $faq_html, 'HTML-ENTITIES', 'UTF-8' ), LIBXML_HTML_NOIMPLIED | LIBXML_HTML_NODEFDTD );
        
        $xpath = new DOMXPath( $dom );
        // O padrão geralmente gerado pelo pipeline Python costuma usar strong, h3 ou divs específicas para perguntas.
        // Vamos procurar os nós que o Python usa como pergunta (assumindo <dt> e <dd> ou similares, mas fallback para dt/dd ou divs com data attributes)
        
        // Se houver os atributos data-question e data-answer conforme sugerido no TODO:
        $faq_items = $xpath->query('//*[@data-question]');
        
        if ( $faq_items->length > 0 ) {
            foreach ( $faq_items as $item ) {
                $question = $item->getAttribute('data-question');
                $answer   = $item->getAttribute('data-answer');
                
                if ( ! empty($question) && ! empty($answer) ) {
                    $faq_schema['mainEntity'][] = array(
                        '@type'          => 'Question',
                        'name'           => wp_strip_all_tags( $question ),
                        'acceptedAnswer' => array(
                            '@type' => 'Answer',
                            'text'  => wp_kses_post( $answer )
                        )
                    );
                }
            }
        } else {
            // Fallback genérico caso o Python use <h3> para pergunta e <p> para resposta
            $headings = $xpath->query('//h3');
            foreach ( $headings as $h3 ) {
                $question = $h3->nodeValue;
                $answer = '';
                $next = $h3->nextSibling;
                while ( $next && $next->nodeName !== 'h3' ) {
                    if ( $next->nodeType === XML_ELEMENT_NODE ) {
                        $answer .= $dom->saveHTML( $next );
                    }
                    $next = $next->nextSibling;
                }
                
                if ( ! empty($question) && ! empty($answer) ) {
                    $faq_schema['mainEntity'][] = array(
                        '@type'          => 'Question',
                        'name'           => wp_strip_all_tags( $question ),
                        'acceptedAnswer' => array(
                            '@type' => 'Answer',
                            'text'  => wp_kses_post( $answer )
                        )
                    );
                }
            }
        }

        if ( ! empty( $faq_schema['mainEntity'] ) ) {
            echo '<script type="application/ld+json">' . wp_json_encode( $faq_schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) . '</script>' . "\n";
        }
    }
});
