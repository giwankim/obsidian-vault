---
title: "Notification"
source: "https://martinfowler.com/eaaDev/Notification.html"
author:
  - "[[Martin Fowler]]"
published: 2004-08-09
created: 2026-10-03
description: "An object that collects together information about errors and other information in the domain layer and communicates it to the presentation."
tags:
  - "clippings"
---

> [!summary]
> Martin Fowler's draft EAA pattern describes a Notification: an object the domain layer uses to collect validation errors, along with warnings and info messages, which it passes back to a separated presentation layer that it can't call directly. Using a notification instead of exceptions lets the domain report every error in one round trip, and error codes shared through a DTO layer supertype let the UI map each error to the matching field. A C# insurance-claim example shows the DTO, the command's validate method, and a form that displays the errors with an `ErrorProvider`.

An object that collects together information about errors and other information in the domain layer and communicates it to the presentation.

This is part of the [Further Enterprise Application Architecture development](https://martinfowler.com/eaaDev) writing that I was doing in the mid 2000’s. Sadly too many other things have claimed my attention since, so I haven’t had time to work on them further, nor do I see much time in the foreseeable future. As such this material is very much in draft form and I won’t be doing any corrections or updates until I’m able to find time to work on it again.

A common application scenario is that of a presentation capturing data from the user and passing submitting that data to the domain for validation. The domain needs to make a number of checks and if any them fail, to let the presentation know about it. However [Separated Presentation](https://martinfowler.com/eaaDev/SeparatedPresentation.html) does not allow the domain to communicate directly with the presentation.

A Notification is an object that the domain uses to collect information about errors during the validation. When an error appears the Notification is sent back to the presentation so the presentation can display further information about the errors.

## How it Works

In its simplest form, a notification can just be a collection of strings which are error messages that the domain generates while it's doing its work. With each validation that the domain layer makes, each failure results in an error added to the notification. However it makes sense to give the notification a more explicit interface than this. A notification object will typically have methods for adding errors that use error codes rather than strings, and convenience methods to tell if the notification has any errors present.

If you are using a [Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html) (DTO), it makes sense to add the notification to the DTO in a [Layer Supertype](https://martinfowler.com/eaaCatalog/layerSupertype.html). This allows all interactions to use the notification cleanly.

If your domain logic is relatively simple, such as using Transaction Scripts, then the logic can have a direct reference to the Notification. This makes it easy to refer to it while adding errors. Referring to the Notification can be more problematic in more layered systems using a [Domain Model](https://martinfowler.com/eaaCatalog/domainModel.html) because such domain models often don't have visibility into such things as incoming DTOs. In this case case it's necessary place a Notification into some kind of session object that domain objects can easily reach.

Error codes need to be present on classes that are shared between presentation and domain. Using error codes provides a more explicit statement of the expected errors and makes it easier for the presentation to present the errors in a more interactive way than just printing out error messages. With a simple domain layer it's often enough to embed these codes within a data transfer object (if you're using one) or a set of error codes for the specific interaction. With a domain model the error codes need to be designed around the vocabulary of the domain model itself.

While errors are usually the most needed aspect for a Notification, it's also useful for the Notification to pass back any other information that the domain wishes to convey to its caller. These might include warnings (problems that aren't serious enough to stop the interaction) and informational messages to display to the user. These need to be separated on the Notification so that the presentation can easily tell if any errors are present.

If you are using Notification in a system where the presentation and domain logic are in different processes, you need to ensure that the Notification only contains information that can be safely transported across the wire, typically this means you cannot embed references to domain objects in such Notification.

When the presentation receives a response from the validation, it needs to check the Notification to determine if there are errors. If so it can pull information out of the Notification to display these errors to the user. If there are errors one option is for the domain to raise an exception so that the presentation can use exception handling to handle the errors. On the whole I feel that validation errors are sufficiently common that it isn't worthwhile to use exception handling mechanisms for these cases, but that's not an overwhelming preference.

## When to Use It

You should use Notification whenever validation is done by a layer of code that cannot have a direct dependency to the module that initiates the validation. This is very common in a layered architecture is [Separated Presentation](https://martinfowler.com/eaaDev/SeparatedPresentation.html).

The most obvious alternative to using Notification is for the domain to use exception handling to indicate errors. Such an approach has the domain throw an exception if a validation check fails. The problem with this is that it only indicates the first validation error. It's usually more helpful to show every validation error, particular if validation requires a round trip to a remote domain layer.

Another alternative is for the domain layer to raise an event for validation errors. This allows multiple errors to be flagged. However it's not so good for remote domain layers since each event would result in a network call.

## Example: Error Checking a Window (C#)

In [Figure 1](#notification_registerClaim.jpg) I have a simplistic form to submit to judge an insurance claim. I have three bits of data to submit: the policy number (a string), the type of claim (text from a pick list), and the date of the incident (a DateTime).

If my data is simplistic, just wait for my validity checks:

- Check that none of the three bits of data are missing (null or blank for the strings.
- Check that the policy number is present in the data store.
- Check that the date of the incident is later than the inception date of the policy.

We want to give as much information back to the user as possible, so if we can reasonably detect multiple errors we should.

I'll start the discussion with the domain layer. The basic interface to the domain logic is in a [Service Layer](https://martinfowler.com/eaaCatalog/serviceLayer.html).

class ClaimService...

```
public void RegisterClaim (RegisterClaimDTO claim) {
  RegisterClaim cmd = new RegisterClaim(claim);
  cmd.Run();
}
```

This method just creates and runs a command object to do the actual work. Wrapping command objects behind a method call service layer can help simplify a server API and make it easier to build a [Remote Facade](https://martinfowler.com/eaaCatalog/remoteFacade.html).

I use a [Data Transfer Object](https://martinfowler.com/eaaCatalog/dataTransferObject.html), to transfer the data over. The RegisterClaimDTO contains the main data.

RegisterClaimDTO: DataTransferObject

```
private string _policyID;
private string _Type;
private DateTime _incidentDate = BLANK_DATE;

public string PolicyId {
  get { return _policyID; }
  set { _policyID = value; }
}
public string Type {
  get { return _Type; }
  set { _Type = value; }
}
public DateTime IncidentDate {
  get { return _incidentDate; }
  set { _incidentDate = value; }
}
```

DataTransferObject is a Layer Supertype for all the DTOs. This contains general code to create and access a Notification to go with the interaction.

class DataTransferObject...

```
private Notification _notification = new Notification();
public Notification Notification {
  get { return _notification; }
  set { _notification = value; }
}
```

The notification class is what we'll use to capture the errors in the domain layer. Essentially it's a collection of errors, each one of which is a simple wrapper around a string.

class Notification...

```
private IList _errors = new ArrayList();

public IList Errors {
  get { return _errors; }
  set { _errors = value; }
}
public bool HasErrors {
  get {return 0 != Errors.Count;}
}
```

class Notification.Error

```
private string message;
public Error(string message) {
  this.message = message;
}
```

The command's run method is very simple.

class class RegisterClaim: ServerCommand...

```
public RegisterClaim(RegisterClaimDTO claim) : base(claim) {}
public void Run() {
  Validate();
  if (!notification.HasErrors)
    RegisterClaimInBackendSystems();
}
```

Again the Layer Supertype provides some general functionality to store the DTO and access the notification.

class ServerCommand...

```
public ServerCommand(DataTransferObject data){
  this._data = data;
}
protected DataTransferObject _data;
protected Notification notification {
  get {return _data.Notification;}
}
```

The validate method carries out the validations that I talked about above. Essentially all it does is run a series of conditional checks, adding errors into the notification if anything fails.

class RegisterClaim...

```
private void Validate() {
  failIfNullOrBlank(Data.PolicyId, RegisterClaimDTO.MISSING_POLICY_NUMBER);
  failIfNullOrBlank(Data.Type, RegisterClaimDTO.MISSING_INCIDENT_TYPE);
  fail (Data.IncidentDate == RegisterClaimDTO.BLANK_DATE, RegisterClaimDTO.MISSING_INCIDENT_DATE);
  if (isNullOrBlank(Data.PolicyId)) return;
  Policy policy = FindPolicy(Data.PolicyId);
  if (policy == null) {
    notification.Errors.Add(RegisterClaimDTO.UNKNOWN_POLICY_NUMBER);
  }
  else {
    fail ((Data.IncidentDate.CompareTo(policy.InceptionDate) < 0),
          RegisterClaimDTO.DATE_BEFORE_POLICY_START);
  }
}
```

The most complex thing about much of this is that certain validation checks only make sense if others haven't failed - which leads to conditional logic in the validate method. With more realistic size methods it's important to break them out into smaller chunks.

Common generic bits of validation can (and should) be extracted and put in the Layer Supertype.

```
protected bool isNullOrBlank(String s) {
  return (s == null || s == "");
}
protected void failIfNullOrBlank (string s, Notification.Error error) {
  fail (isNullOrBlank(s), error);
}
protected void fail(bool condition, Notification.Error error) {
  if (condition) notification.Errors.Add(error);
}
```

The very simplest form of error for the Notification would be just to use strings as error messages. I prefer at least a minimal wrapping, defining a simple error class and defining a fixed list of errors for the interaction in the DTO.

class RegisterClaimDTO...

```
public static Notification.Error MISSING_POLICY_NUMBER = new Notification.Error("Policy number is missing");
public static Notification.Error UNKNOWN_POLICY_NUMBER = new Notification.Error("This policy number is unknown");
public static Notification.Error MISSING_INCIDENT_TYPE = new Notification.Error("Incident type is missing");
public static Notification.Error MISSING_INCIDENT_DATE = new Notification.Error("Incident Date is missing");
public static Notification.Error DATE_BEFORE_POLICY_START
  = new Notification.Error("Incident Date is before we started doing this business");
```

If you are communicating across tiers you may need to add an ID field to the error to allow comparisons to work properly when errors are being serialized across the wire.

That pretty much is all the interesting behavior in the domain layer. For the presentation I'll use an [Autonomous View](https://martinfowler.com/eaaDev/AutonomousView.html). The behavior we're interested in occurs when the submit button is pressed.

class FrmRegisterClaim...

```
RegisterClaimDTO claim;
public void Submit() {
  saveToClaim();
  service.RegisterClaim(claim);
  if (claim.Notification.HasErrors) {
    txtResponse.Text = "Not registered, see errors";
    indicateErrors();
  }
  else txtResponse.Text = "Registration Succeeded";
}
private void saveToClaim() {
  claim = new RegisterClaimDTO();
  claim.PolicyId = txtPolicyNumber.Text;
  claim.IncidentDate = pkIncidentDate.Value;
  claim.Type = (string) cmbType.SelectedItem;
}
```

The method pulls information out of the controls to fill the DTO and sends the data to the domain layer. If the returning DTO contais errors, then we need to display them.

class FrmRegisterClaim...

```
private void indicateErrors() {
  checkError(RegisterClaimDTO.MISSING_POLICY_NUMBER, txtPolicyNumber);
  checkError(RegisterClaimDTO.MISSING_INCIDENT_TYPE, cmbType);
  checkError(RegisterClaimDTO.DATE_BEFORE_POLICY_START, pkIncidentDate);
  checkError(RegisterClaimDTO.MISSING_INCIDENT_DATE, pkIncidentDate);
  checkError(RegisterClaimDTO.DATE_BEFORE_POLICY_START, pkIncidentDate);
}
private void checkError (Notification.Error error, Control control) {
  if (claim.Notification.IncludesError(error))
    showError(control, error.ToString());
}
```

Here I'm using the errors defined in the DTO and mapping them to fields in the form, so the right field shows the right errors.

To actually display the errors, I use the standard error provider that comes with.NET. This displays an error icon next to fields in trouble, and a tooltip to reveal the error message that's the cause of the problem.

class FrmRegisterClaim...

```
private ErrorProvider errorProvider = new ErrorProvider();
void showError (Control arg, string message) {
  errorProvider.SetError(arg, message);
}
```

I clear the error information if anything in the fields change.

class FrmRegisterClaim...

```
void clearError (Control arg) {
  errorProvider.SetError(arg, null);
}
private void txtPolicyNumber_TextChanged(object sender, EventArgs e) {
  clearError((Control)sender);
}
private void cmbType_TextChanged(object sender, EventArgs e) {
  clearError((Control)sender);
}
private void pkIncidentDate_ValueChanged(object sender, EventArgs e) {
  clearError((Control)sender);
}
```
