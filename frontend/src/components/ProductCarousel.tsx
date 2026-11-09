import React, { useRef } from 'react'
import {
  Star,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Package,
  Tag,
} from 'lucide-react'
import type { Product } from '../types'

interface ProductCarouselProps {
  products: Product[]
}

export const ProductCarousel: React.FC<ProductCarouselProps> = ({ products }) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  if (!products || products.length === 0) {
    return null
  }

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = 300
      scrollContainerRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      })
    }
  }

  const formatDiscount = (discount?: number): string | null => {
    if (discount === undefined || discount === null || discount <= 0) return null
    const pct = discount <= 1.0 ? Math.round(discount * 100) : Math.round(discount)
    return pct > 0 ? `${pct}% OFF` : null
  }

  const formatRatingsCount = (count?: number): string => {
    if (!count) return ''
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k reviews`
    }
    return `${count} reviews`
  }

  return (
    <div className="product-carousel-wrapper">
      <div className="product-carousel-header">
        <div className="carousel-title">
          <Package className="w-4 h-4 text-primary" size={16} />
          <span>Found {products.length} {products.length === 1 ? 'Product' : 'Products'}</span>
        </div>
        {products.length > 2 && (
          <div className="carousel-controls">
            <button
              onClick={() => scroll('left')}
              className="carousel-nav-btn"
              title="Scroll left"
              type="button"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => scroll('right')}
              className="carousel-nav-btn"
              title="Scroll right"
              type="button"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      <div className="product-carousel-track" ref={scrollContainerRef}>
        {products.map((item, index) => {
          const discountStr = formatDiscount(item.discount)
          const hasImage = Boolean(item.image_url)

          return (
            <div key={index} className="product-card">
              {/* Product Visual / Image Container */}
              <div className="product-image-container">
                {hasImage ? (
                  <img
                    src={item.image_url}
                    alt={item.title || 'Product'}
                    className="product-image"
                    onError={(e) => {
                      // Fallback to placeholder if image fails to load
                      e.currentTarget.style.display = 'none'
                      const fallback = e.currentTarget.parentElement?.querySelector(
                        '.product-image-fallback'
                      ) as HTMLElement
                      if (fallback) fallback.style.display = 'flex'
                    }}
                  />
                ) : null}

                <div
                  className="product-image-fallback"
                  style={{ display: hasImage ? 'none' : 'flex' }}
                >
                  <Package size={36} className="product-placeholder-icon" />
                  <span className="product-brand-chip">{item.brand || 'Product'}</span>
                </div>

                {discountStr && (
                  <span className="product-discount-badge">
                    <Tag size={11} className="mr-1" />
                    {discountStr}
                  </span>
                )}
              </div>

              {/* Product Information */}
              <div className="product-details">
                <div className="product-brand-row">
                  <span className="product-brand-name">{item.brand || 'Unbranded'}</span>
                  {item.avg_rating !== undefined && item.avg_rating !== null && (
                    <div className="product-rating">
                      <Star size={13} className="star-icon fill-gold" />
                      <span className="rating-num">{item.avg_rating}</span>
                      {item.total_ratings ? (
                        <span className="rating-count">({formatRatingsCount(item.total_ratings)})</span>
                      ) : null}
                    </div>
                  )}
                </div>

                <h4 className="product-title" title={item.title}>
                  {item.title || 'Untitled Product'}
                </h4>

                <div className="product-footer">
                  <div className="product-pricing">
                    <span className="price-symbol">₹</span>
                    <span className="price-amount">
                      {typeof item.price === 'number'
                        ? item.price.toLocaleString('en-IN')
                        : item.price || 'N/A'}
                    </span>
                  </div>

                  {item.product_link ? (
                    <a
                      href={item.product_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="product-cta-btn"
                      title="View product details on Flipkart"
                    >
                      <span>Buy</span>
                      <ExternalLink size={13} />
                    </a>
                  ) : null}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
