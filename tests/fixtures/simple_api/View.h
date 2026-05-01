class BView : public BHandler {
public:
    BView(BRect frame);
    virtual void Draw(BRect update);
};

struct rgb_color {};

enum orientation {};
