# Materiały kontekstowe

Mobile: karty jedna pod drugą, jedna miniatura i link do pełnej galerii.

## Properties

- `Rozmiar` (variant): Desktop | Mobile — default Desktop

## Variants

### Rozmiar=Desktop

- box "Rozmiar=Desktop" · flex-column · gap var(--space-24) · w 1312px, h hug
  - **Nagłówek sekcji** {Pokaż licznik=false, Pokaż opis=true, Opis=“Opracowania i materiały wizualne związane z utworem”, Licznik=“2 z 24”, Tytuł=“Materiały kontekstowe”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - box "Karty" · flex-row · gap var(--space-24) · w fill, h hug
    - box "Teksty sekundarne" · flex-column · gap var(--space-8) · padding var(--space-24) · w fill, h fill · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
      - **Nagłówek kolumny** {Pokaż liczbę=true, Liczba=“3”, Etykieta=“Teksty sekundarne”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“01”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“02”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“03”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
    - box "Materiały wizualne" · flex-column · gap var(--space-16) · padding var(--space-24) · w fill, h fill · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
      - **Nagłówek kolumny** {Pokaż liczbę=true, Liczba=“3”, Etykieta=“Materiały wizualne”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - box "Miniatury" · flex-row · gap var(--space-16) · w fill, h hug
        - **Miniatura materiału** {Podpis=“[Podpis], ML, sygn. [numer]”} · flex-column · gap var(--space-8) · w 176px, h hug
        - **Miniatura materiału** {Podpis=“[Podpis], ML, sygn. [numer]”} · flex-column · gap var(--space-8) · w 176px, h hug
        - **Miniatura materiału** {Podpis=“[Podpis], ML, sygn. [numer]”} · flex-column · gap var(--space-8) · w 176px, h hug

### Rozmiar=Mobile

- box "Rozmiar=Mobile" · flex-column · gap var(--space-24) · w 358px, h hug
  - **Nagłówek sekcji** {Pokaż licznik=false, Pokaż opis=true, Opis=“Opracowania i materiały wizualne związane z utworem”, Licznik=“2 z 24”, Tytuł=“Materiały kontekstowe”} · flex-column · gap var(--space-8) · padding 0px 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
  - box "Karty" · flex-column · gap var(--space-24) · w fill, h hug
    - box "Teksty sekundarne" · flex-column · gap var(--space-8) · padding var(--space-24) · w fill, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
      - **Nagłówek kolumny** {Pokaż liczbę=true, Liczba=“3”, Etykieta=“Teksty sekundarne”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“01”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“02”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - **Pozycja bibliograficzna** {Wydanie=“[Wydawnictwo], [miejsce] [rok], s. [strony]”, Opis=“[Autor], [Tytuł opracowania]”, Nr=“03”} · flex-row · gap var(--space-12) · padding var(--space-12) 0px var(--space-12) 0px · w fill, h hug · border-bottom 1px var(--color-border-subtle)
    - box "Materiały wizualne" · flex-column · gap var(--space-16) · padding var(--space-24) · w fill, h hug · bg var(--color-bg-card) · border 1px var(--color-border-subtle) · radius var(--radius-m) · shadow var(--shadow-karta)
      - **Nagłówek kolumny** {Pokaż liczbę=true, Liczba=“3”, Etykieta=“Materiały wizualne”} · flex-row · padding 0px 0px var(--space-8) 0px · justify space-between · align center · w fill, h hug · border-bottom 1px var(--color-border-subtle)
      - box "Miniatury" · flex-row · gap var(--space-16) · w fill, h hug
        - **Miniatura materiału** {Podpis=“[Podpis], ML, sygn. [numer]”} · flex-column · gap var(--space-8) · w 176px, h hug
      - **Link ze strzałką [Stan=Domyślny]** {Etykieta=“Wszystkie materiały wizualne (3)”, Stan=“Domyślny”} · flex-row · gap var(--space-4) · align center · w hug, h hug

Preview: `../previews/components/materialy-kontekstowe.png`
