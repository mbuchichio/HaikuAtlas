class BApplication : public BLooper {
public:
								BApplication(const char* signature);
	virtual						~BApplication();

	static	BArchivable*		Instantiate(BMessage* data);
	virtual	status_t			Archive(BMessage* data, bool deep = true) const;

	virtual	thread_id			Run();
	virtual	void				Quit();
	virtual bool				QuitRequested();
	virtual	void				MessageReceived(BMessage* message);

private:
	virtual	void				_ReservedApplication1();
};
