TEMPLATES = {
    "business": {
        "id": "business",
        "name": "Business/Corporate",
        "description": "Professional business website with services, about, and contact sections",
        "category": "Business",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "features", "about", "testimonials", "contact"],
                },
                {"slug": "services", "title": "Services", "sections": ["services-grid", "cta"]},
                {"slug": "about", "title": "About Us", "sections": ["about-content", "team"]},
                {"slug": "contact", "title": "Contact", "sections": ["contact-form", "map"]},
            ],
            "theme": {
                "primary_color": "#2563EB",
                "secondary_color": "#1E40AF",
                "font": "Inter",
                "dark_mode": True,
            },
        },
    },
    "portfolio": {
        "id": "portfolio",
        "name": "Portfolio",
        "description": "Personal portfolio for creatives with project gallery and skills",
        "category": "Personal",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "work", "skills", "contact"],
                },
                {"slug": "projects", "title": "Projects", "sections": ["project-gallery"]},
            ],
            "theme": {
                "primary_color": "#7C3AED",
                "secondary_color": "#6D28D9",
                "font": "Inter",
                "dark_mode": True,
            },
        },
    },
    "ngo": {
        "id": "ngo",
        "name": "NGO/Charity",
        "description": "Non-profit website with donation, volunteer registration, and impact stories",
        "category": "Non-Profit",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "impact-stats", "featured-causes", "cta-donate"],
                },
                {"slug": "about", "title": "About", "sections": ["mission", "team", "partners"]},
                {"slug": "causes", "title": "Our Causes", "sections": ["causes-grid"]},
                {"slug": "volunteer", "title": "Volunteer", "sections": ["volunteer-form"]},
                {"slug": "donate", "title": "Donate", "sections": ["donate-form"]},
                {"slug": "blog", "title": "Blog", "sections": ["blog-list"]},
                {"slug": "contact", "title": "Contact", "sections": ["contact-form"]},
            ],
            "theme": {
                "primary_color": "#22C55E",
                "secondary_color": "#16A34A",
                "font": "Inter",
                "dark_mode": False,
            },
        },
    },
    "ecommerce": {
        "id": "ecommerce",
        "name": "E-Commerce",
        "description": "Online store with product catalog, cart, and checkout",
        "category": "Business",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "featured-products", "categories", "newsletter"],
                },
                {"slug": "shop", "title": "Shop", "sections": ["product-grid", "filters"]},
                {"slug": "product", "title": "Product", "sections": ["product-detail"]},
                {"slug": "cart", "title": "Cart", "sections": ["cart-content"]},
                {"slug": "checkout", "title": "Checkout", "sections": ["checkout-form"]},
            ],
            "theme": {
                "primary_color": "#F59E0B",
                "secondary_color": "#D97706",
                "font": "Inter",
                "dark_mode": False,
            },
        },
    },
    "restaurant": {
        "id": "restaurant",
        "name": "Restaurant",
        "description": "Restaurant website with menus, reservations, and location",
        "category": "Business",
        "frameworks": ["html-css", "react"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "specials", "about-chef", "reviews"],
                },
                {"slug": "menu", "title": "Menu", "sections": ["menu-categories"]},
                {"slug": "reservations", "title": "Reservations", "sections": ["reservation-form"]},
                {"slug": "contact", "title": "Contact", "sections": ["location", "hours", "contact-form"]},
            ],
            "theme": {
                "primary_color": "#EF4444",
                "secondary_color": "#DC2626",
                "font": "Playfair Display",
                "dark_mode": False,
            },
        },
    },
    "hotel": {
        "id": "hotel",
        "name": "Hotel & Travel",
        "description": "Hotel website with room booking, amenities, and travel info",
        "category": "Business",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "rooms-preview", "amenities", "location-highlights"],
                },
                {"slug": "rooms", "title": "Rooms", "sections": ["room-grid", "booking-form"]},
                {"slug": "amenities", "title": "Amenities", "sections": ["amenities-grid"]},
                {"slug": "gallery", "title": "Gallery", "sections": ["gallery-grid"]},
                {"slug": "contact", "title": "Contact", "sections": ["contact-form", "map"]},
            ],
            "theme": {
                "primary_color": "#06B6D4",
                "secondary_color": "#0891B2",
                "font": "Inter",
                "dark_mode": False,
            },
        },
    },
    "school": {
        "id": "school",
        "name": "School/Education",
        "description": "School website with courses, admissions, events, and faculty",
        "category": "Education",
        "frameworks": ["html-css", "react", "nextjs"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "about-school", "programs", "events"],
                },
                {"slug": "about", "title": "About", "sections": ["history", "mission", "faculty"]},
                {"slug": "programs", "title": "Programs", "sections": ["program-list"]},
                {"slug": "admissions", "title": "Admissions", "sections": ["admissions-info", "apply-form"]},
                {"slug": "events", "title": "Events", "sections": ["event-calendar"]},
                {"slug": "contact", "title": "Contact", "sections": ["contact-form"]},
            ],
            "theme": {
                "primary_color": "#2563EB",
                "secondary_color": "#7C3AED",
                "font": "Inter",
                "dark_mode": False,
            },
        },
    },
    "healthcare": {
        "id": "healthcare",
        "name": "Healthcare",
        "description": "Medical practice website with services, appointments, and patient resources",
        "category": "Business",
        "frameworks": ["html-css", "react"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "services", "why-choose-us", "testimonials"],
                },
                {"slug": "services", "title": "Services", "sections": ["service-detail"]},
                {"slug": "doctors", "title": "Our Doctors", "sections": ["doctor-grid"]},
                {"slug": "appointments", "title": "Book Appointment", "sections": ["appointment-form"]},
                {"slug": "contact", "title": "Contact", "sections": ["contact-info", "map"]},
            ],
            "theme": {
                "primary_color": "#22C55E",
                "secondary_color": "#06B6D4",
                "font": "Inter",
                "dark_mode": False,
            },
        },
    },
    "saas": {
        "id": "saas",
        "name": "SaaS Startup",
        "description": "SaaS landing page with features, pricing, and signup",
        "category": "Business",
        "frameworks": ["html-css", "react", "nextjs", "vue"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Home",
                    "sections": ["hero", "features", "how-it-works", "pricing", "faq", "cta"],
                },
                {"slug": "features", "title": "Features", "sections": ["feature-detail"]},
                {"slug": "pricing", "title": "Pricing", "sections": ["pricing-table"]},
                {"slug": "docs", "title": "Documentation", "sections": ["docs-content"]},
                {"slug": "blog", "title": "Blog", "sections": ["blog-list"]},
            ],
            "theme": {
                "primary_color": "#7C3AED",
                "secondary_color": "#2563EB",
                "font": "Inter",
                "dark_mode": True,
            },
        },
    },
    "landing": {
        "id": "landing",
        "name": "Landing Page",
        "description": "Modern single-page landing page for products and campaigns",
        "category": "Marketing",
        "frameworks": ["html-css", "react", "nextjs", "vue"],
        "structure": {
            "pages": [
                {
                    "slug": "index",
                    "title": "Landing",
                    "sections": ["hero", "features", "testimonials", "pricing", "faq", "cta"],
                },
            ],
            "theme": {
                "primary_color": "#2563EB",
                "secondary_color": "#7C3AED",
                "font": "Inter",
                "dark_mode": True,
            },
        },
    },
}
