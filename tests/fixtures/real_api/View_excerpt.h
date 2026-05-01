class BView : public BHandler {
public:
								BView(const char* name, uint32 flags,
									BLayout* layout = NULL);
								BView(BRect frame, const char* name,
									uint32 resizingMode, uint32 flags);
	virtual						~BView();

	static	BArchivable*		Instantiate(BMessage* archive);
	virtual	status_t			Archive(BMessage* archive,
									bool deep = true) const;
	virtual	void				AttachedToWindow();
	virtual	void				Draw(BRect updateRect);
	virtual	void				MouseDown(BPoint where);

private:
	virtual	void				_ReservedView1();
};
