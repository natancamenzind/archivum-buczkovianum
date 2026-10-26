# Wyszukiwanie — panel filtrów (mobile)

Viewport: mobile, 390px wide. Preview: `../previews/screens/wyszukiwanie-panel-filtrow-mobile.png`

- box "Wyszukiwanie — panel filtrów (mobile)" · flex-column · gap 0px · 390px × 844px · bg var(--color-bg-page)
  - box "Nagłówek panelu" · flex-row · padding var(--space-12) var(--layout-page-margin-mobile) var(--space-12) var(--layout-page-margin-mobile) · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
    - text "Tytuł" · .text-lora-tytul-sekcji · color var(--color-text-primary) · “Filtry”
    - box "Zamknij" · flex-row · gap 0px · justify center · align center · w 44px, h 44px
      - **Ikona/zamknij** · w 16px, h 16px
  - box "Grupy filtrów" · flex-column · gap var(--space-32) · padding var(--space-24) var(--layout-page-margin-mobile) var(--space-48) var(--layout-page-margin-mobile) · w fill, h hug
    - box "Utwór" · flex-column · gap var(--space-8) · w fill, h hug
      - **Nagłówek kolumny** {Pokaż liczbę=true, Liczba=“2”, Etykieta=“Utwór”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pole wyboru [Zaznaczone=Nie]** {Pokaż liczbę=true, Liczba=“2”, Etykieta=“Wertepy”, Zaznaczone=“Nie”} · flex-row · gap var(--space-8) · align center · w hug, h hug
      - **Pole wyboru [Zaznaczone=Nie]** {Pokaż liczbę=true, Liczba=“1”, Etykieta=“Czarny potok”, Zaznaczone=“Nie”} · flex-row · gap var(--space-8) · align center · w hug, h hug
    - box "Dostępność" · flex-column · gap var(--space-8) · w fill, h hug
      - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Dostępność”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pole wyboru [Zaznaczone=Nie]** {Pokaż liczbę=true, Liczba=“3”, Etykieta=“Ze skanem”, Zaznaczone=“Nie”} · flex-row · gap var(--space-8) · align center · w hug, h hug
      - **Pole wyboru [Zaznaczone=Nie]** {Pokaż liczbę=true, Liczba=“0”, Etykieta=“Z transkrypcją”, Zaznaczone=“Nie”} · flex-row · gap var(--space-8) · align center · w hug, h hug
    - box "Okres" · flex-column · gap var(--space-8) · w fill, h hug
      - **Nagłówek kolumny** {Pokaż liczbę=false, Liczba=“3”, Etykieta=“Okres”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Lista rozwijana** {Wartość=“Wszystkie lata”} · flex-row · padding var(--space-8) var(--space-12) var(--space-8) var(--space-12) · justify space-between · align center · w fill, h hug · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
  - box "Odstęp" · flex-column · gap 0px · w fill, h fill
  - box "Akcje" · flex-row · gap var(--space-12) · padding var(--space-16) var(--layout-page-margin-mobile) var(--space-16) var(--layout-page-margin-mobile) · w fill, h hug · bg var(--color-bg-page) · border-top 1px var(--color-border-subtle)
    - **Przycisk [Rodzaj=Drugorzędny, Stan=Domyślny]** {Etykieta=“Wyczyść”, Rodzaj=“Drugorzędny”, Stan=“Domyślny”} · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w fill, h 44px · bg var(--color-bg-card) · border 1px var(--color-border-accent) · radius var(--radius-s)
    - **Przycisk [Rodzaj=Główny, Stan=Domyślny]** {Etykieta=“Pokaż wyniki (7)”, Rodzaj=“Główny”, Stan=“Domyślny”} · flex-row · gap 0px · padding 0px var(--space-24) 0px var(--space-24) · justify center · align center · w fill, h 44px · bg var(--color-bg-accent) · radius var(--radius-s)
