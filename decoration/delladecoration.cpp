// SPDX-License-Identifier: MIT
// Della window decoration: one translucent surface shared by the titlebar and the
// application body (Kvantum paints the body with the same tint), KDE-standard buttons.
#include <KDecoration3/DecoratedWindow>
#include <KDecoration3/Decoration>
#include <KDecoration3/DecorationButton>
#include <KDecoration3/DecorationButtonGroup>
#include <KDecoration3/DecorationSettings>
#include <KDecoration3/DecorationShadow>
#include <KDecoration3/ScaleHelpers>

#include <KConfig>
#include <KConfigGroup>
#include <KPluginFactory>

#include <QHash>
#include <QPainter>
#include <QPainterPath>
#include <QVariantAnimation>

#include <cmath>
#include <vector>

namespace Della
{
using KDecoration3::DecorationButtonType;

struct Theme {
    QColor tint;
    qreal opacity = 0.5;
    QColor text;
    qreal radius = 8;
    qreal titleHeight = 36;
    bool light = false;
};

// ~/.config/dellarc is written by the Della settings app and installer.
static Theme loadTheme()
{
    KConfig config(QStringLiteral("dellarc"), KConfig::SimpleConfig);
    const KConfigGroup g(&config, QStringLiteral("Glass"));
    Theme t;
    t.light = g.readEntry("Mode", QStringLiteral("dark")) == QLatin1String("light");
    t.tint = QColor(g.readEntry(t.light ? "LightTint" : "DarkTint", t.light ? QStringLiteral("#f5f6f9") : QStringLiteral("#1b1e26")));
    t.opacity = std::clamp(g.readEntry(t.light ? "LightOpacity" : "DarkOpacity", t.light ? 0.62 : 0.5), 0.05, 1.0);
    t.text = t.light ? QColor(26, 28, 34) : QColor(244, 246, 250);
    t.radius = std::max(0.0, g.readEntry("Radius", 8.0));
    t.titleHeight = std::max(24.0, g.readEntry("TitleHeight", 36.0));
    return t;
}

// Separable box blur, three passes approximate a gaussian. Only alpha matters (black shadow).
static void blurAlpha(std::vector<float> &a, int w, int h, int radius)
{
    std::vector<float> tmp(a.size());
    for (int pass = 0; pass < 3; ++pass) {
        for (int y = 0; y < h; ++y) {
            float sum = 0;
            for (int x = -radius; x <= radius; ++x) {
                sum += a[y * w + std::clamp(x, 0, w - 1)];
            }
            for (int x = 0; x < w; ++x) {
                tmp[y * w + x] = sum / (2 * radius + 1);
                sum += a[y * w + std::min(x + radius + 1, w - 1)] - a[y * w + std::max(x - radius, 0)];
            }
        }
        for (int x = 0; x < w; ++x) {
            float sum = 0;
            for (int y = -radius; y <= radius; ++y) {
                sum += tmp[std::clamp(y, 0, h - 1) * w + x];
            }
            for (int y = 0; y < h; ++y) {
                a[y * w + x] = sum / (2 * radius + 1);
                sum += tmp[std::min(y + radius + 1, h - 1) * w + x] - tmp[std::max(y - radius, 0) * w + x];
            }
        }
    }
}

// Soft, lifted macOS-like shadow. The area under the window is cut out so the glass is not darkened.
static std::shared_ptr<KDecoration3::DecorationShadow> shadowFor(qreal radius, bool active, bool light)
{
    static QHash<QString, std::shared_ptr<KDecoration3::DecorationShadow>> cache;
    const QString key = QStringLiteral("%1-%2-%3").arg(radius).arg(active).arg(light);
    if (auto it = cache.constFind(key); it != cache.constEnd()) {
        return *it;
    }
    const int extent = active ? 64 : 40;
    const int offset = active ? 16 : 8;
    const int box = 2 * int(std::ceil(radius)) + 2;
    const int size = box + 2 * extent;

    QImage shape(size, size, QImage::Format_ARGB32_Premultiplied);
    shape.fill(Qt::transparent);
    {
        QPainter p(&shape);
        p.setRenderHint(QPainter::Antialiasing);
        p.setPen(Qt::NoPen);
        p.setBrush(Qt::black);
        p.drawRoundedRect(QRectF(extent, extent + offset, box, box), radius, radius);
    }
    std::vector<float> alpha(size * size);
    for (int y = 0; y < size; ++y) {
        const QRgb *line = reinterpret_cast<const QRgb *>(shape.constScanLine(y));
        for (int x = 0; x < size; ++x) {
            alpha[y * size + x] = qAlpha(line[x]);
        }
    }
    blurAlpha(alpha, size, size, (extent - offset) / 3);
    const float strength = (active ? 0.62f : 0.38f) * (light ? 0.6f : 1.0f);
    QImage image(size, size, QImage::Format_ARGB32_Premultiplied);
    for (int y = 0; y < size; ++y) {
        QRgb *line = reinterpret_cast<QRgb *>(image.scanLine(y));
        for (int x = 0; x < size; ++x) {
            line[x] = qRgba(0, 0, 0, int(std::min(255.0f, alpha[y * size + x] * strength)));
        }
    }
    {
        QPainter p(&image);
        p.setRenderHint(QPainter::Antialiasing);
        p.setCompositionMode(QPainter::CompositionMode_DestinationOut);
        p.setPen(Qt::NoPen);
        p.setBrush(Qt::black);
        p.drawRoundedRect(QRectF(extent, extent, box, box), radius + 0.5, radius + 0.5);
    }
    auto shadow = std::make_shared<KDecoration3::DecorationShadow>();
    shadow->setPadding(QMarginsF(extent, extent, extent, extent));
    shadow->setInnerShadowRect(QRectF(image.rect().center(), QSizeF(1, 1)));
    shadow->setShadow(image);
    cache.insert(key, shadow);
    return shadow;
}

class Decoration : public KDecoration3::Decoration
{
    Q_OBJECT
public:
    explicit Decoration(QObject *parent = nullptr, const QVariantList &args = QVariantList())
        : KDecoration3::Decoration(parent, args)
    {
    }

    bool init() override;
    void paint(QPainter *painter, const QRectF &repaintArea) override;

    const Theme &theme() const
    {
        return m_theme;
    }
    QColor fontColor() const
    {
        QColor c = m_theme.text;
        if (!window()->isActive()) {
            c.setAlphaF(0.55);
        }
        return c;
    }
    QColor solidTint() const
    {
        return m_theme.tint;
    }

private:
    void reconfigure();
    void createButtons();
    void updateLayout();
    void updateShadow();
    QPainterPath titlePath() const;
    bool isFlat() const
    {
        return window()->isMaximized();
    }

    Theme m_theme;
    KDecoration3::DecorationButtonGroup *m_left = nullptr;
    KDecoration3::DecorationButtonGroup *m_right = nullptr;
};

class Button : public KDecoration3::DecorationButton
{
    Q_OBJECT
public:
    Button(QObject *parent, const QVariantList &args)
        : Button(args.at(0).value<DecorationButtonType>(), args.at(1).value<Decoration *>(), parent)
    {
        setGeometry(QRectF(0, 0, 24, 24));
    }

    Button(DecorationButtonType type, Decoration *decoration, QObject *parent = nullptr)
        : KDecoration3::DecorationButton(type, decoration, parent)
        , m_animation(new QVariantAnimation(this))
    {
        m_animation->setDuration(150);
        m_animation->setEasingCurve(QEasingCurve::InOutQuad);
        connect(m_animation, &QVariantAnimation::valueChanged, this, [this](const QVariant &v) {
            m_hover = v.toReal();
            update();
        });
        connect(this, &KDecoration3::DecorationButton::hoveredChanged, this, [this](bool hovered) {
            m_animation->stop();
            m_animation->setStartValue(m_hover);
            m_animation->setEndValue(hovered ? 1.0 : 0.0);
            m_animation->start();
        });
        connect(decoration->window(), &KDecoration3::DecoratedWindow::iconChanged, this, [this] {
            update();
        });
    }

    static KDecoration3::DecorationButton *create(DecorationButtonType type, KDecoration3::Decoration *decoration, QObject *parent)
    {
        auto d = qobject_cast<Decoration *>(decoration);
        if (!d) {
            return nullptr;
        }
        auto b = new Button(type, d, parent);
        auto w = d->window();
        using W = KDecoration3::DecoratedWindow;
        switch (type) {
        case DecorationButtonType::Close:
            b->setVisible(w->isCloseable());
            connect(w, &W::closeableChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::Maximize:
            b->setVisible(w->isMaximizeable());
            connect(w, &W::maximizeableChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::Minimize:
            b->setVisible(w->isMinimizeable());
            connect(w, &W::minimizeableChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::ContextHelp:
            b->setVisible(w->providesContextHelp());
            connect(w, &W::providesContextHelpChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::Shade:
            b->setVisible(w->isShadeable());
            connect(w, &W::shadeableChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::OnAllDesktops:
            b->setVisible(d->settings()->isOnAllDesktopsAvailable());
            connect(d->settings().get(), &KDecoration3::DecorationSettings::onAllDesktopsAvailableChanged, b, &Button::setVisible);
            break;
        case DecorationButtonType::ApplicationMenu:
            b->setVisible(w->hasApplicationMenu());
            connect(w, &W::hasApplicationMenuChanged, b, &Button::setVisible);
            break;
        default:
            break;
        }
        return b;
    }

    void paint(QPainter *painter, const QRectF &) override
    {
        auto d = qobject_cast<Decoration *>(decoration());
        if (!d || !isVisible()) {
            return;
        }
        const QRectF rect = geometry();
        painter->save();
        painter->setRenderHint(QPainter::Antialiasing);

        if (type() == DecorationButtonType::Menu) {
            const qreal icon = std::min<qreal>(16, rect.width());
            const QRectF iconRect(rect.center() - QPointF(icon / 2, icon / 2), QSizeF(icon, icon));
            d->window()->icon().paint(painter, iconRect.toRect());
            painter->restore();
            return;
        }

        // Breeze geometry: an 18px circle on a 20px grid, scaled to the button.
        const qreal width = rect.width();
        painter->translate(rect.topLeft());
        painter->scale(width / 20, width / 20);
        painter->translate(1, 1);

        const QColor font = d->fontColor();
        const QColor red(237, 85, 95);
        const bool close = type() == DecorationButtonType::Close;
        const bool toggled = isChecked()
            && (type() == DecorationButtonType::KeepAbove || type() == DecorationButtonType::KeepBelow || type() == DecorationButtonType::Shade
                || type() == DecorationButtonType::OnAllDesktops);
        const qreal fill = isPressed() || toggled ? 1.0 : m_hover;

        QColor foreground = font;
        if (fill > 0) {
            QColor background = close ? (isPressed() ? red.darker(125) : red) : font;
            background.setAlphaF(background.alphaF() * fill * (isPressed() && !close ? 0.75 : 1.0));
            painter->setPen(Qt::NoPen);
            painter->setBrush(background);
            painter->drawEllipse(QRectF(0, 0, 18, 18));
            // Glyph turns into the glass color, like Breeze's titlebar-colored glyph.
            const QColor glyph = close ? QColor(255, 255, 255) : d->solidTint();
            foreground = QColor::fromRgbF(font.redF() + (glyph.redF() - font.redF()) * fill,
                                          font.greenF() + (glyph.greenF() - font.greenF()) * fill,
                                          font.blueF() + (glyph.blueF() - font.blueF()) * fill,
                                          font.alphaF() + (1.0 - font.alphaF()) * fill);
        }
        if (!isEnabled()) {
            foreground.setAlphaF(foreground.alphaF() * 0.4);
        }

        QPen pen(foreground);
        pen.setCapStyle(Qt::RoundCap);
        pen.setJoinStyle(Qt::MiterJoin);
        pen.setWidthF(1.01 * std::max<qreal>(1.0, 20 / width));
        painter->setPen(pen);
        painter->setBrush(Qt::NoBrush);

        switch (type()) {
        case DecorationButtonType::Close:
            painter->drawLine(QPointF(5, 5), QPointF(13, 13));
            painter->drawLine(QPointF(13, 5), QPointF(5, 13));
            break;
        case DecorationButtonType::Maximize:
            if (isChecked()) {
                pen.setJoinStyle(Qt::RoundJoin);
                painter->setPen(pen);
                painter->drawPolygon(QList<QPointF>{QPointF(4, 9), QPointF(9, 4), QPointF(14, 9), QPointF(9, 14)});
            } else {
                painter->drawPolyline(QList<QPointF>{QPointF(4, 11), QPointF(9, 6), QPointF(14, 11)});
            }
            break;
        case DecorationButtonType::Minimize:
            painter->drawPolyline(QList<QPointF>{QPointF(4, 7), QPointF(9, 12), QPointF(14, 7)});
            break;
        case DecorationButtonType::OnAllDesktops:
            painter->setPen(Qt::NoPen);
            painter->setBrush(foreground);
            if (isChecked()) {
                painter->drawEllipse(QRectF(6, 6, 6, 6));
            } else {
                painter->drawPolygon(QList<QPointF>{QPointF(6.5, 8.5), QPointF(12, 3), QPointF(15, 6), QPointF(9.5, 11.5)});
                painter->setPen(pen);
                painter->drawLine(QPointF(5.5, 7.5), QPointF(10.5, 12.5));
                painter->drawLine(QPointF(12, 6), QPointF(4.5, 13.5));
            }
            break;
        case DecorationButtonType::Shade:
            painter->drawLine(QPointF(4, 5.5), QPointF(14, 5.5));
            if (isChecked()) {
                painter->drawPolyline(QList<QPointF>{QPointF(4, 8), QPointF(9, 13), QPointF(14, 8)});
            } else {
                painter->drawPolyline(QList<QPointF>{QPointF(4, 13), QPointF(9, 8), QPointF(14, 13)});
            }
            break;
        case DecorationButtonType::KeepBelow:
            painter->drawPolyline(QList<QPointF>{QPointF(4, 5), QPointF(9, 10), QPointF(14, 5)});
            painter->drawPolyline(QList<QPointF>{QPointF(4, 9), QPointF(9, 14), QPointF(14, 9)});
            break;
        case DecorationButtonType::KeepAbove:
            painter->drawPolyline(QList<QPointF>{QPointF(4, 9), QPointF(9, 4), QPointF(14, 9)});
            painter->drawPolyline(QList<QPointF>{QPointF(4, 13), QPointF(9, 8), QPointF(14, 13)});
            break;
        case DecorationButtonType::ApplicationMenu:
            painter->drawLine(QPointF(4, 5), QPointF(14, 5));
            painter->drawLine(QPointF(4, 9), QPointF(14, 9));
            painter->drawLine(QPointF(4, 13), QPointF(14, 13));
            break;
        case DecorationButtonType::ContextHelp: {
            QPainterPath path;
            path.moveTo(5, 6);
            path.arcTo(QRectF(5, 3.5, 8, 5), 180, -180);
            path.cubicTo(QPointF(12.5, 9.5), QPointF(9, 7.5), QPointF(9, 11.5));
            painter->drawPath(path);
            painter->drawPoint(QPointF(9, 15));
            break;
        }
        default:
            break;
        }
        painter->restore();
    }

private:
    QVariantAnimation *m_animation;
    qreal m_hover = 0;
};

bool Decoration::init()
{
    m_theme = loadTheme();
    auto s = settings();
    auto w = window();
    using W = KDecoration3::DecoratedWindow;
    connect(s.get(), &KDecoration3::DecorationSettings::reconfigured, this, &Decoration::reconfigure);
    connect(s.get(), &KDecoration3::DecorationSettings::fontChanged, this, &Decoration::updateLayout);
    connect(s.get(), &KDecoration3::DecorationSettings::decorationButtonsLeftChanged, this, &Decoration::createButtons);
    connect(s.get(), &KDecoration3::DecorationSettings::decorationButtonsRightChanged, this, &Decoration::createButtons);
    connect(w, &W::activeChanged, this, [this] {
        updateShadow();
        update();
    });
    connect(w, &W::captionChanged, this, [this] {
        update(titleBar());
    });
    connect(w, &W::widthChanged, this, &Decoration::updateLayout);
    connect(w, &W::maximizedChanged, this, &Decoration::updateLayout);
    connect(w, &W::adjacentScreenEdgesChanged, this, &Decoration::updateLayout);
    connect(w, &W::shadedChanged, this, &Decoration::updateLayout);
    connect(w, &W::nextScaleChanged, this, &Decoration::updateLayout);
    createButtons();
    updateShadow();
    return true;
}

void Decoration::reconfigure()
{
    m_theme = loadTheme();
    updateLayout();
    updateShadow();
    update();
}

void Decoration::createButtons()
{
    delete m_left;
    delete m_right;
    m_left = new KDecoration3::DecorationButtonGroup(KDecoration3::DecorationButtonGroup::Position::Left, this, &Button::create);
    m_right = new KDecoration3::DecorationButtonGroup(KDecoration3::DecorationButtonGroup::Position::Right, this, &Button::create);
    updateLayout();
}

void Decoration::updateShadow()
{
    setShadow(shadowFor(m_theme.radius, window()->isActive(), m_theme.light));
}

QPainterPath Decoration::titlePath() const
{
    const QRectF bar(0, 0, size().width(), borderTop());
    QPainterPath path;
    const qreal r = isFlat() ? 0 : std::min(m_theme.radius, bar.height());
    if (r <= 0) {
        path.addRect(bar);
        return path;
    }
    path.moveTo(bar.bottomLeft());
    path.lineTo(bar.left(), bar.top() + r);
    path.arcTo(QRectF(bar.left(), bar.top(), 2 * r, 2 * r), 180, -90);
    path.lineTo(bar.right() - r, bar.top());
    path.arcTo(QRectF(bar.right() - 2 * r, bar.top(), 2 * r, 2 * r), 90, -90);
    path.lineTo(bar.bottomRight());
    path.closeSubpath();
    return path;
}

void Decoration::updateLayout()
{
    if (!m_left || !m_right) {
        return;
    }
    const qreal scale = window()->nextScale();
    const bool flat = isFlat();
    const qreal title = KDecoration3::snapToPixelGrid(m_theme.titleHeight, scale);
    setBorders(QMarginsF(0, title, 0, 0));
    const qreal grab = flat ? 0 : KDecoration3::snapToPixelGrid(6, scale);
    setResizeOnlyBorders(QMarginsF(grab, grab, grab, grab));

    const qreal r = flat ? 0 : KDecoration3::snapToPixelGrid(m_theme.radius, scale);
    setBorderRadius(KDecoration3::BorderRadius(r, r, r, r));
    if (flat || !settings()->isAlphaChannelSupported()) {
        setBorderOutline(KDecoration3::BorderOutline());
    } else {
        // Hairline glass edge around the whole window, drawn by KWin on the rounded shape.
        // KWin blends the outline color as premultiplied alpha.
        const qreal a = m_theme.light ? 0.14 : 0.16;
        const int level = m_theme.light ? 0 : int(255 * a);
        const QColor edge(level, level, level, int(255 * a));
        setBorderOutline(KDecoration3::BorderOutline(KDecoration3::pixelSize(scale), edge, KDecoration3::BorderRadius(r, r, r, r)));
    }
    setTitleBar(QRectF(0, 0, size().width(), title));
    setBlurRegion(QRegion(titlePath().toFillPolygon().toPolygon()));

    const qreal button = KDecoration3::snapToPixelGrid(std::min<qreal>(24, title - 8), scale);
    const qreal side = KDecoration3::snapToPixelGrid(flat ? 8 : 12, scale);
    const qreal top = KDecoration3::snapToPixelGrid((title - button) / 2, scale);
    for (auto group : {m_left, m_right}) {
        group->setSpacing(KDecoration3::snapToPixelGrid(4, scale));
        for (auto b : group->buttons()) {
            b->setGeometry(QRectF(QPointF(0, 0), QSizeF(button, button)));
        }
    }
    m_left->setPos(QPointF(side, top));
    m_right->setPos(QPointF(size().width() - side - m_right->geometry().width(), top));
    update();
}

void Decoration::paint(QPainter *painter, const QRectF &repaintArea)
{
    const bool alpha = settings()->isAlphaChannelSupported();
    const QRectF bar(0, 0, size().width(), borderTop());
    const QPainterPath path = titlePath();

    painter->save();
    painter->setRenderHint(QPainter::Antialiasing);
    painter->setPen(Qt::NoPen);
    QColor fill = m_theme.tint;
    fill.setAlphaF(alpha ? m_theme.opacity : 1.0);
    painter->fillPath(path, fill);

    if (alpha && !isFlat()) {
        // Light catching on the top glass edge: brightest in the middle, fading into the corners.
        QLinearGradient edge(bar.topLeft(), bar.topRight());
        const int peak = m_theme.light ? 200 : 90;
        edge.setColorAt(0.0, QColor(255, 255, 255, 0));
        edge.setColorAt(0.5, QColor(255, 255, 255, peak));
        edge.setColorAt(1.0, QColor(255, 255, 255, 0));
        const qreal px = KDecoration3::pixelSize(window()->scale());
        painter->fillRect(QRectF(m_theme.radius, 0, bar.width() - 2 * m_theme.radius, px), edge);
    }

    if (bar.intersects(repaintArea)) {
        QFont font = settings()->font();
        font.setWeight(QFont::Bold);
        painter->setFont(font);
        painter->setPen(fontColor());
        const qreal gap = 10;
        const qreal left = m_left->buttons().isEmpty() ? 16 : m_left->geometry().right() + gap;
        const qreal right = m_right->buttons().isEmpty() ? bar.width() - 16 : m_right->geometry().left() - gap;
        const QFontMetricsF metrics(font);
        const QString caption = window()->caption();
        const qreal textWidth = metrics.horizontalAdvance(caption);
        QRectF text(0, 0, bar.width(), bar.height());
        // Centered on the window when it fits, otherwise centered in the space between buttons.
        if ((bar.width() - textWidth) / 2 < left || (bar.width() + textWidth) / 2 > right) {
            text = QRectF(left, 0, std::max<qreal>(0, right - left), bar.height());
        }
        painter->drawText(text, Qt::AlignCenter | Qt::TextSingleLine, metrics.elidedText(caption, Qt::ElideRight, text.width()));
    }
    painter->restore();

    m_left->paint(painter, repaintArea);
    m_right->paint(painter, repaintArea);
}
} // namespace Della

K_PLUGIN_FACTORY_WITH_JSON(DellaDecorationFactory, "della.json", registerPlugin<Della::Decoration>(); registerPlugin<Della::Button>();)

#include "delladecoration.moc"
